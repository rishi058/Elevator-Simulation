from .direction import Direction
from .stop_scheduler import StopScheduler
import uuid

class UIStateManager(StopScheduler):
    """Manages UI state for button lighting"""
    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        self.ui_external_up_requests = set()
        self.ui_external_down_requests = set()
        self.ui_internal_requests = set()
    
    def add_request(self, input_floor: int, input_dir: str):
        if input_dir == Direction.UP:
            self.ui_external_up_requests.add(input_floor)
        else:
            self.ui_external_down_requests.add(input_floor)
        
        request_uuid = str(uuid.uuid4())
        return super().add_request(input_floor, input_dir, request_uuid)
    
    def add_stop(self, floor: int):
        self.ui_internal_requests.add(floor)
        # Propagate to StopScheduler
        return super().add_stop(floor)

    def remove_request(self, request_uuid: str):
        # Call Parent: Returns (floor, direction) or None
        result = super().remove_request(request_uuid)  # returns (floor, direction)
        
        if result is not None:
            floor, direction = result
            
            # Remove from UI sets
            if direction == Direction.UP:
                self.ui_external_up_requests.discard(floor)
            elif direction == Direction.DOWN:
                self.ui_external_down_requests.discard(floor)
            
            # Return True to indicate success to the Controller
            return True
            
        return False
    
    def update_ui_requests(self):
        if not self.is_door_open:
            return
        
        dir = self.get_effective_direction()
        floor = self.current_floor

        # Always clear internal request for this floor
        self.ui_internal_requests.discard(floor)
        
        if dir == Direction.IDLE:
            self.ui_external_up_requests.discard(floor)
            self.ui_external_down_requests.discard(floor)
            return

        # UP ARRIVAL
        if dir == Direction.UP:
            if floor in self.ui_external_up_requests:
                self.ui_external_up_requests.discard(floor)
            
            # Turnaround Logic: Clear DOWN request if no more UP stops exist
            if floor in self.ui_external_down_requests:
                if not self.has_requests_above(floor):
                    self.ui_external_down_requests.discard(floor)

        # DOWN ARRIVAL
        elif dir == Direction.DOWN:
            if floor in self.ui_external_down_requests:
                self.ui_external_down_requests.discard(floor)
            
            # Turnaround Logic: Clear UP request if no more DOWN stops exist
            if floor in self.ui_external_up_requests:
                if not self.has_requests_below(floor):
                    self.ui_external_up_requests.discard(floor)