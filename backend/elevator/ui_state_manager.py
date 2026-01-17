from .direction import Direction
from .stop_scheduler import StopScheduler

class UIStateManager(StopScheduler):
    """Manages UI state for button lighting"""
    
    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        self.ui_external_up_requests = set()
        self.ui_external_down_requests = set()
        self.ui_internal_requests = set()
    
    def add_request(self, input_floor: int, input_dir: str):
        if input_dir == Direction.UP:
            self.ui_external_up_requests.add(input_floor)
        else:
            self.ui_external_down_requests.add(input_floor)
        # Propagate to StopScheduler
        super().add_request(input_floor, input_dir)
    
    def add_stop(self, floor: int):
        self.ui_internal_requests.add(floor)
        # Propagate to StopScheduler
        super().add_stop(floor)
    
    def update_ui_requests(self):
        if not self.is_door_open:
            return
        
        dir = self.get_effective_direction()
        floor = self.current_floor

        if floor in self.ui_internal_requests:
            self.ui_internal_requests.discard(floor)
        
        if dir == Direction.UP and floor in self.ui_external_up_requests:
            self.ui_external_up_requests.discard(floor)

        elif dir == Direction.DOWN and floor in self.ui_external_down_requests:
            self.ui_external_down_requests.discard(floor)
       
        else:  # IDLE
            self.ui_external_up_requests.discard(floor)
            self.ui_external_down_requests.discard(floor)