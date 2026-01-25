from math import floor
from elevator.direction import Direction
from elevator.base_elevator import BaseElevator
import asyncio
import heapq

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, val):
        if val not in self.heap: heapq.heappush(self.heap, val)

    def extract_min(self):
        if not self.heap: return None
        return heapq.heappop(self.heap)  # Pop the smallest item off the heap,
    
    def get_min(self):
        if not self.heap: return None
        return self.heap[0]  # The smallest item is at the root of the heap  
    
class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, val):
        # Invert value for max-heap behavior
        if -val not in self.heap: heapq.heappush(self.heap, -val) 

    def extract_max(self):
        if not self.heap: return None
        return -heapq.heappop(self.heap)  # Pop the largest item off the heap,
    
    def get_max(self):
        if not self.heap: return None
        return -self.heap[0]  # The largest item is at the root of the heap

#!---------------------------------------------------------------------------------------------

class StopScheduler(BaseElevator):    
    """
    LOOK Elevator Scheduling Algorithm.
    1. Services requests in one direction until no more remain.
    2. Then reverses direction and services requests on the way back.
    """
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
    
    # --- HELPERS FOR UI STATE MANAGER ---

    def has_requests_above(self, floor: int) -> bool:
        max_down = self.down_stops.get_max()
        if max_down is not None and max_down > floor:
            return True
        
        if any(f > floor for f in self.up_stops.heap):
            return True 
  
        return False 

    def has_requests_below(self, floor: int) -> bool:
        min_up = self.up_stops.get_min()
        if min_up is not None and min_up < floor:
            return True 
        
        if any(-f_neg < floor for f_neg in self.down_stops.heap):
            return True
            
        return False