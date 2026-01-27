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

    def sync_ui_state(self):
        """
        Synchronize UI state with scheduler trees.
        Remove any floors from UI sets that are no longer in any scheduler tree.
        This prevents ghost values from race conditions between get_next_stop and remove_request.
        """
        # Check UP requests - floor should exist in up_up or down_up trees
        floors_to_remove_up = []
        for floor in self.ui_external_up_requests:
            if (self.up_up.find(floor) is None and 
                self.down_up.find(floor) is None):
                floors_to_remove_up.append(floor)
        
        for floor in floors_to_remove_up:
            self.ui_external_up_requests.discard(floor)
        
        # Check DOWN requests - floor should exist in down_down or up_down trees
        floors_to_remove_down = []
        for floor in self.ui_external_down_requests:
            if (self.down_down.find(floor) is None and 
                self.up_down.find(floor) is None):
                floors_to_remove_down.append(floor)
        
        for floor in floors_to_remove_down:
            self.ui_external_down_requests.discard(floor)