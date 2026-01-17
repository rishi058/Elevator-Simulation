from .direction import Direction
from .base_elevator import BaseElevator
from .heap import MinHeap, MaxHeap
import asyncio

class StopScheduler(BaseElevator):    
    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        self.up_stops = MinHeap()
        self.down_stops = MaxHeap()
    
    def add_request(self, input_floor: int, input_dir: str):
        eff_dir = self.get_effective_direction()

        # IDLE ELEVATOR
        if eff_dir == Direction.IDLE:
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

        # MOVING UP
        if eff_dir == Direction.UP:
            if input_floor >= self.current_floor and input_dir == Direction.UP:
                self.up_stops.insert(input_floor)
            else:
                self.down_stops.insert(input_floor)
            return

        # MOVING DOWN
        if eff_dir == Direction.DOWN:
            if input_floor <= self.current_floor and input_dir == Direction.DOWN:
                self.down_stops.insert(input_floor)
            else:
                self.up_stops.insert(input_floor)

    def add_stop(self, floor: int):
        eff_dir = self.get_effective_direction()

        if floor == self.current_floor:
            if not self.is_door_open:
                asyncio.create_task(self.open_door())
            return

        # IDLE
        if eff_dir == Direction.IDLE:
            if floor > self.current_floor:
                self.up_stops.insert(floor)
                self.direction = Direction.UP
            else:
                self.down_stops.insert(floor)
                self.direction = Direction.DOWN
            return

        # MOVING UP
        if eff_dir == Direction.UP:
            if floor > self.current_floor:
                self.up_stops.insert(floor)
            else:
                self.down_stops.insert(floor)
            return

        # MOVING DOWN
        if eff_dir == Direction.DOWN:
            if floor < self.current_floor:
                self.down_stops.insert(floor)
            else:
                self.up_stops.insert(floor)

    def get_next_stop(self, delete: bool = True):
        eff_dir = self.get_effective_direction()

        if eff_dir == Direction.UP:
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

        if eff_dir == Direction.DOWN:
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