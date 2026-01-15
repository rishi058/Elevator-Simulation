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
#!------------------------------------------------------------------------------  
        # For UI Purpose to light on/off buttons 
        self.ui_external_up_requests = set()  
        self.ui_external_down_requests = set()  

        self.ui_internal_requests = set()  
#!------------------------------------------------------------------------------  
        # Callback for state broadcast (set by controller)
        self.on_state_change = None

    def update_ui_requests(self):
        if self.current_floor in self.ui_internal_requests:
            self.ui_internal_requests.discard(self.current_floor)
        # -----------------------------------------------------
        if self.direction == Direction.UP:
            if self.current_floor in self.ui_external_up_requests:
                self.ui_external_up_requests.discard(self.current_floor)
            else:
                self.ui_external_down_requests.discard(self.current_floor)

        elif self.direction == Direction.DOWN:
            if self.current_floor in self.ui_external_down_requests:
                self.ui_external_down_requests.discard(self.current_floor)
            else:
                self.ui_external_up_requests.discard(self.current_floor)

        else:  # IDLE
            self.ui_external_up_requests.discard(self.current_floor)
            self.ui_external_down_requests.discard(self.current_floor)


    def add_request(self, input_floor: int, input_dir: str):
        if input_dir == Direction.UP:
            self.ui_external_up_requests.add(input_floor)
        else:
            self.ui_external_down_requests.add(input_floor)

        effective_direction = self.get_effective_direction()

        # ─────────────────────────────
        # IDLE ELEVATOR
        # ─────────────────────────────
        if effective_direction == Direction.IDLE:
            if input_floor == self.current_floor:
                if not self.is_door_open:
                    asyncio.create_task(self.open_door())
                return
            
            if input_floor > self.current_floor:
                self.up_stops.insert(input_floor)
                self.direction = Direction.UP
            else:
                self.down_stops.insert(input_floor)
                self.direction = Direction.DOWN
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

    # Effective-Direction is IDLE, Request is for Same Floor 
    async def open_door(self):
        self.is_door_open = True
        await asyncio.sleep(5)  # Door open for 5 seconds
        self.is_door_open = False

    def add_stop(self, floor: int):
        self.ui_internal_requests.add(floor)

        effective_direction = self.get_effective_direction()

        if floor == self.current_floor:
            if not self.is_door_open:
                asyncio.create_task(self.open_door())
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
                await self._notify_state_change() #! Broadcast state change
                await asyncio.sleep(1)
                continue  

            self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            await self._notify_state_change() #! Broadcast state change

            while self.is_door_open:  # wait for door to close before moving
                await asyncio.sleep(1)

            self.update_ui_requests()

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
            self.update_ui_requests()
            self.direction = Direction.IDLE  # Set idle while door is open
            await self._notify_state_change() #! Broadcast state change
            await asyncio.sleep(5)  # Door open for 5 seconds
            self.is_door_open = False
            await self._notify_state_change() #! Broadcast state change

    #!---------------------------------------------------------------------------------
    
    async def _notify_state_change(self): # Notify Controller about state change
        if self.on_state_change:
            await self.on_state_change(self)
    
    def get_status(self) -> dict:
        return {
            "elevator_id": self.id,
            "current_floor": self.current_floor,
            "direction": self.get_effective_direction(),
            "is_door_open": self.is_door_open,
            "external_up_requests": list(self.ui_external_up_requests),
            "external_down_requests": list(self.ui_external_down_requests),
            "internal_requests": list(self.ui_internal_requests),
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