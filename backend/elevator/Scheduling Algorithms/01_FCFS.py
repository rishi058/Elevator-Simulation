from elevator.direction import Direction 
from elevator.base_elevator import BaseElevator
import asyncio

class StopScheduler(BaseElevator):   
    """
    True FCFS (First-Come, First-Served) Elevator Scheduling Algorithm.
    Requests are strictly handled in the order of arrival.
    """

    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        # We use a single queue for ALL stops to maintain strict time ordering
        self.queue = [] 

    def add_stop(self, floor: int):
        # Passenger inside presses a button
        if floor not in self.queue:
            self.queue.append(floor)

    def add_request(self, input_floor: int, input_dir: str):
        # Person outside calls elevator
        if input_floor == self.current_floor and self.is_door_open:
            return # Already here
            
        if input_floor == self.current_floor and not self.is_door_open:
             asyncio.create_task(self.open_door())
             return

        if input_floor not in self.queue:
            self.queue.append(input_floor)

    def get_next_stop(self, delete: bool = False):
        if not self.queue:
            return None
        
        # STRICT FCFS: Always take the first item in the list
        next_stop = self.queue[0]
        
        # Remove it from the queue so we don't process it again
        if delete: self.queue.pop(0)

        # Update direction simply based on target
        if next_stop > self.current_floor:
            self.direction = Direction.UP
        elif next_stop < self.current_floor:
            self.direction = Direction.DOWN
        else:
            self.direction = Direction.IDLE
            
        return next_stop