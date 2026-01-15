from .direction import Direction
from .heap import MinHeap, MaxHeap
import asyncio
import copy

class Elevator: 
    def __init__(self, total_floors=10):
        self.total_floors = total_floors   #! Used for validation fast-api methods
        self.current_floor = 0  # Can be float during movement (e.g., 1.25)
        self.direction = Direction.IDLE
        self.up_stops = MinHeap()
        self.down_stops = MaxHeap()

        self.is_door_open = False
        self.moving_direction = Direction.IDLE
#!------------------------------------------------------------------------------   
        self.ws_manager = None  # WebSocket manager will be set later
        self.prev_state = None  # Track previous state for broadcast optimization

    def set_websocket_manager(self, ws_manager):
        """Set the WebSocket manager for broadcasting updates"""
        self.ws_manager = ws_manager
    
    async def broadcast_state(self):
        if self.ws_manager is None:
            return

        moving_direction = self.direction
        if moving_direction == Direction.IDLE and self.is_door_open:
            moving_direction = self.moving_direction

        loop = asyncio.get_running_loop()

        state = {
            "current_floor": self.current_floor,
            "direction": moving_direction,
            "is_door_open": self.is_door_open,
            "timestamp": loop.time()
        }

        if self.prev_state:
            if {k: v for k, v in state.items() if k != "timestamp"} == \
            {k: v for k, v in self.prev_state.items() if k != "timestamp"}:
                return

        await self.ws_manager.broadcast(state)
        self.prev_state = copy.deepcopy(state)
#!------------------------------------------------------------------------------   
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

    # Effective-Direction is IDLE, Request is for Same Floor 
    async def open_door(self):
        self.is_door_open = True
        await asyncio.sleep(5)  # Door open for 5 seconds
        self.is_door_open = False

    def add_stop(self, floor: int):
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
                await self.broadcast_state()  #! Broadcast idle state
                await asyncio.sleep(1)
                continue  

            self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            await self.broadcast_state()  #! Broadcast direction change

            while self.is_door_open:  # wait for door to close before moving
                await asyncio.sleep(1)

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

                print(f"[Elevator Moving] Current Floor: {self.current_floor}")
                await self.broadcast_state()  #! Broadcast position update
                await asyncio.sleep(1)   # this will take 5 seconds to move one floor

            self.current_floor = int(self.current_floor)  # Ensure exact floor value
            print(f"[Elevator] Arrived at floor: {self.current_floor}")
            self.is_door_open = True
            self.moving_direction = self.direction
            self.direction = Direction.IDLE  # Set idle while door is open
            await self.broadcast_state()  #! Broadcast arrival with door open
            await asyncio.sleep(5)  # Door open for 5 seconds
            self.is_door_open = False
            await self.broadcast_state()  #! Broadcast door close

    def cleanup(self):
        self.total_floors = 0
        self.current_floor = 0  
        self.direction = Direction.IDLE
        self.is_door_open = False
        self.moving_direction = Direction.IDLE
        self.up_stops = None
        self.down_stops = None
        self.ws_manager = None 