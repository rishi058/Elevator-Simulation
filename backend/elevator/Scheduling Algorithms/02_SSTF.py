from elevator.direction import Direction 
from elevator.base_elevator import BaseElevator
import asyncio

class StopScheduler(BaseElevator):   
    """
    SSTF (Shortest Seek Time First) / Nearest Car Algorithm.
    1. Selects the request closest to the current floor.
    2. Ignores direction and time of arrival.
    """

    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        # We merge internal and external requests effectively for calculation
        self.queue = set() 

    def add_stop(self, floor: int):
        self.queue.add(floor)

    def add_request(self, input_floor: int, input_dir: str):
        if input_floor == self.current_floor:
            if not self.is_door_open: asyncio.create_task(self.open_door())
            return
        self.queue.add(input_floor)

    def get_next_stop(self, delete: bool = False):
        if not self.queue:
            return None
        
        # --- THE CORE LOGIC ---
        # Find the floor in the queue with the minimum absolute difference 
        # from the current floor.
        
        # lambda function: for every 'floor' in queue, calculate abs(floor - current)
        next_stop = min(self.queue, key=lambda floor: abs(floor - self.current_floor))
        
        if delete: self.queue.remove(next_stop)

        # Set direction simply for the display/movement logic
        if next_stop > self.current_floor:
            self.direction = Direction.UP
        elif next_stop < self.current_floor:
            self.direction = Direction.DOWN
        else:
            self.direction = Direction.IDLE
            
        return next_stop