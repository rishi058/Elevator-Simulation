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
        
        #! Generate a unique UUID for tracking
        request_uuid = str(uuid.uuid4())
        return super().add_request(input_floor, input_dir, request_uuid)
    
    def add_stop(self, floor: int):
        self.ui_internal_requests.add(floor)

        # Internal stops: usually don't need tracking IDs
        #! Generate a dummy UUID
        dummy_uuid = f"int_{floor}_{uuid.uuid4().hex[:4]}"
        return super().add_stop(floor, dummy_uuid)

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
        floor = self.current_floor
        
        # Always clear internal request for this floor
        self.ui_internal_requests.discard(floor)

        # Check UP External Requests
        # If it's in UI set but NOT in Scheduler trees, it means it was handled/removed.
        if floor in self.ui_external_up_requests:
            in_up_up = self.up_up.find(floor) is not None
            in_down_up = self.down_up.find(floor) is not None
            
            if not in_up_up and not in_down_up:
                self.ui_external_up_requests.discard(floor)

        # Check DOWN External Requests
        if floor in self.ui_external_down_requests:
            in_down_down = self.down_down.find(floor) is not None
            in_up_down = self.up_down.find(floor) is not None

            if not in_down_down and not in_up_down:
                self.ui_external_down_requests.discard(floor)