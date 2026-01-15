from .direction import Direction
from .heap import MinHeap, MaxHeap
import asyncio

class Elevator: 
    def __init__(self, elevator_id: int, total_floors: int = 10):
        self.id = elevator_id
        self.total_floors = total_floors  #! UseLess
        self.current_floor = 0  # Can be float during movement (e.g., 1.25)
        self.direction = Direction.IDLE
        self.up_stops = MinHeap()
        self.down_stops = MaxHeap()

        self.is_door_open = False
        self.moving_direction = Direction.IDLE
        
        # Callback for state broadcast (set by controller)
        self.on_state_change = None


    def add_request(self, input_floor: int, input_dir: str):
        effective_direction = self.get_effective_direction()

        # ─────────────────────────────
        # IDLE ELEVATOR
        # ─────────────────────────────
        if effective_direction == Direction.IDLE:
            self.add_stop(input_floor)
            return

        # ─────────────────────────────
        # MOVING UP
        # ─────────────────────────────
        if effective_direction == Direction.UP:
            if input_floor >= self.current_floor and input_dir == Direction.UP:
                self.up_stops.insert(input_floor)
            else:
                self.down_stops.insert(input_floor)
            return

        # ─────────────────────────────
        # MOVING DOWN
        # ─────────────────────────────
        if effective_direction == Direction.DOWN:
            if input_floor <= self.current_floor and input_dir == Direction.DOWN:
                self.down_stops.insert(input_floor)
            else:
                self.up_stops.insert(input_floor)

    def add_stop(self, floor: int):
        effective_direction = self.get_effective_direction()

        if floor == self.current_floor:
            return

        # ─────────────────────────────
        # IDLE
        # ─────────────────────────────
        if effective_direction == Direction.IDLE:
            if floor > self.current_floor:
                self.up_stops.insert(floor)
                self.direction = Direction.UP
            else:
                self.down_stops.insert(floor)
                self.direction = Direction.DOWN
            return

        # ─────────────────────────────
        # MOVING UP
        # ─────────────────────────────
        if effective_direction == Direction.UP:
            if floor > self.current_floor:
                self.up_stops.insert(floor)
            else:
                self.down_stops.insert(floor)
            return

        # ─────────────────────────────
        # MOVING DOWN
        # ─────────────────────────────
        if effective_direction == Direction.DOWN:
            if floor < self.current_floor:
                self.down_stops.insert(floor)
            else:
                self.up_stops.insert(floor)

    def get_effective_direction(self):
        """
        After completing a move_to we generally set Direction.IDLE...
        But At a Intermediate stop we set IDLE only for 2 sec
        """
        if self.direction != Direction.IDLE:
            return self.direction
        if self.is_door_open == True:
            return self.moving_direction
        return Direction.IDLE

    def get_next_stop(self, delete: bool=False):
        effective_direction = self.get_effective_direction()

        if effective_direction == Direction.UP:
            next_up = self.up_stops.get_min()
            if next_up is not None:
                if delete:
                    self.up_stops.extract_min()
                return next_up
            
            next_down = self.down_stops.get_max()
            if next_down is not None:
                if delete:
                    self.down_stops.extract_max()
                return next_down
            
            return None

        if effective_direction == Direction.DOWN:
            next_down = self.down_stops.get_max()
            if next_down is not None:
                if delete:
                    self.down_stops.extract_max()
                return next_down
            
            next_up = self.up_stops.get_min()
            if next_up is not None:
                if delete:
                    self.up_stops.extract_min()
                return next_up
            
            return None
        
        # IDLE - prefer up
        next_up = self.up_stops.get_min()
        if next_up is not None:
            if delete:
                self.up_stops.extract_min()
            return next_up
        
        next_down = self.down_stops.get_max()
        if next_down is not None:
            if delete:
                self.down_stops.extract_max()
            return next_down
        
        return None
    
    async def run(self):
        
        while True:
            stop = self.get_next_stop(delete=True)
            if stop is None:
                self.direction = Direction.IDLE
                await asyncio.sleep(1)
                continue  

            self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN

            while int(self.current_floor) != stop: 
                # Check if there's a closer stop in the same direction
                new_stop = self.get_next_stop()  # delete = False
                if new_stop is not None:
                    # For UP: closer stop is smaller (but still >= current)
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        self.get_next_stop(delete=True)  # Remove from heap
                        self.up_stops.insert(stop)  # Re-add old stop
                        stop = new_stop
                    # For DOWN: closer stop is larger (but still <= current)
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        self.get_next_stop(delete=True)  # Remove from heap
                        self.down_stops.insert(stop)  # Re-add old stop
                        stop = new_stop

                if self.direction == Direction.UP:
                    self.current_floor += 0.2
                    self.current_floor = round(self.current_floor, 1)
                else:
                    self.current_floor -= 0.2
                    self.current_floor = round(self.current_floor, 1)
                
                print(f"Elevator {self.id} moving to floor {self.current_floor}")
                await self._notify_state_change() #! Broadcast state change
                await asyncio.sleep(1)   # this will take 5 seconds to move one floor

            self.current_floor = int(self.current_floor)  # Ensure exact floor value
            self.is_door_open = True
            self.moving_direction = self.direction
            self.direction = Direction.IDLE  # Set idle while door is open
            await self._notify_state_change() #! Broadcast state change
            await asyncio.sleep(5)  # Door open for 5 seconds
            self.is_door_open = False
            await self._notify_state_change() #! Broadcast state change

    #!---------------------------------------------------------------------------------
    
    async def _notify_state_change(self):
        """Notify controller about state change for broadcasting"""
        if self.on_state_change:
            await self.on_state_change(self)
    
    def get_status(self) -> dict:
        """Get current elevator status as dictionary"""
        moving_direction = self.direction
        if moving_direction == Direction.IDLE and self.is_door_open:
            moving_direction = self.moving_direction
        
        return {
            "elevator_id": self.id,
            "current_floor": self.current_floor,
            "direction": moving_direction,
            "is_door_open": self.is_door_open,
            "up_stops": list(self.up_stops.heap),
            "down_stops": list(self.down_stops.heap)
        }
    
    #!---------------------------------------------------------------------------------
    
    def cleanup(self):
        self.id = None
        self.total_floors = None 
        self.current_floor = None
        self.direction = None
        self.up_stops = None
        self.down_stops = None
        self.is_door_open = None
        self.moving_direction = None
        self.on_state_change = None 