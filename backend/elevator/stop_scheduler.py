from .direction import Direction
from .base_elevator import BaseElevator
from .avl_tree import AVLTree
import asyncio

class StopScheduler(BaseElevator):    
    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        
        # --- Internal Requests (Car Buttons) ---
        self.internal_up = AVLTree()
        self.internal_down = AVLTree()

        # --- External Requests (Hall Buttons) ---
        self.up_up = AVLTree()     # [Phase 1] Going UP, want UP
        self.down_down = AVLTree() # [Phase 1] Going DOWN, want DOWN
        
        self.up_down = AVLTree()   # [Phase 2] Going UP, want DOWN (Turnaround)
        self.down_up = AVLTree()   # [Phase 2] Going DOWN, want UP (Turnaround)

#!---------------------------------------------------------------------------------------------

    def add_request(self, input_floor: int, input_dir: str):
        curr = self.current_floor
        eff_dir = self.get_effective_direction()
        
        # IDLE: Sort based on intent
        if eff_dir == Direction.IDLE:
            if input_floor > curr:
                if input_dir == Direction.UP: self.up_up.insert(input_floor)
                else: self.up_down.insert(input_floor)
                self.direction = Direction.UP
            elif input_floor < curr:
                if input_dir == Direction.DOWN: self.down_down.insert(input_floor)
                else: self.down_up.insert(input_floor)
                self.direction = Direction.DOWN
            else:
                if not self.is_door_open: asyncio.create_task(self.open_door())
            return

        # MOVING: Sort based on Phase 1 (Standard) vs Phase 2 (Turnaround)
        if eff_dir == Direction.UP:
            if input_floor >= curr:
                if input_dir == Direction.UP: self.up_up.insert(input_floor)
                else: self.up_down.insert(input_floor)
            else:
                self.down_up.insert(input_floor) # Missed

        elif eff_dir == Direction.DOWN:
            if input_floor <= curr:
                if input_dir == Direction.DOWN: self.down_down.insert(input_floor)
                else: self.down_up.insert(input_floor)
            else:
                self.up_down.insert(input_floor) # Missed

#!---------------------------------------------------------------------------------------------

    def add_stop(self, floor: int):
        if floor > self.current_floor:
            self.internal_up.insert(floor)
            if self.direction == Direction.IDLE: self.direction = Direction.UP
        elif floor < self.current_floor:
            self.internal_down.insert(floor)
            if self.direction == Direction.IDLE: self.direction = Direction.DOWN

#!---------------------------------------------------------------------------------------------

    # external RUN loop likely relies on the function returning None to trigger state changes (like going to IDLE)

    def get_next_stop(self, delete:bool = True):

        # --- IDLE LOGIC ---
        if self.direction == Direction.IDLE:
            # 1. Check for ANY motivation to go UP (Internal OR External)
            iu = self.internal_up.get_min()
            uu = self.up_up.get_min()

            if iu is not None or uu is not None:
                self.direction = Direction.UP
                # We call the helper to ensure we pick the closest stop (Priority 0 vs 1)
                return self._process_up_logic(delete, only_same_direction=False)
            
            # 2. Check for ANY motivation to go DOWN (Internal OR External)
            id_ = self.internal_down.get_max()
            dd = self.down_down.get_max()
  
            if id_ is not None or dd is not None:
                self.direction = Direction.DOWN
                # We call the helper to ensure we pick the closest stop
                return self._process_down_logic(delete, only_same_direction=False)

            # Phase 2: Handle Turnarounds
            # If we wake up for a turnaround, we must manually bypass the "same direction" barrier
            ud = self.up_down.get_max()
            if ud is not None:
                # Call helper with False to allow Phase 2 access
                self.direction = Direction.UP
                return self._process_up_logic(delete, only_same_direction=False)
            
            du = self.down_up.get_min()
            if du is not None:
                # Call helper with False to allow Phase 2 access
                self.direction = Direction.DOWN
                return self._process_down_logic(delete, only_same_direction=False)
            
            return None

        # --- ACTIVE LOGIC ---
        if self.direction == Direction.UP:
            return self._process_up_logic(delete, only_same_direction=True)
        
        if self.direction == Direction.DOWN:
            return self._process_down_logic(delete, only_same_direction=True)
        
        return None

    def _process_up_logic(self, delete: bool, only_same_direction: bool):
        PRIO_INTERNAL, PRIO_EXTERNAL, PRIO_MISSED = 0, 1, 2

        iu = self.internal_up.get_min()
        uu = self.up_up.get_min()
        du = self.down_up.get_min()

        candidates = []
        # Phase 1: Standard UP requests
        if iu is not None: candidates.append((iu, PRIO_INTERNAL))
        if uu is not None: candidates.append((uu, PRIO_EXTERNAL))
        if du is not None and du > self.current_floor:           # Check for 'Missed' requests (down_up > current_floor)
            candidates.append((du, PRIO_MISSED))

        if candidates:
            target, priority = min(candidates, key=lambda x: (x[0], x[1]))
            if delete:
                if priority == PRIO_INTERNAL: self.internal_up.delete_min()
                elif priority == PRIO_EXTERNAL: self.up_up.delete_min()
                else: self.down_up.delete_min()   # PRIO_MISSED
            return target

        #! THE BARRIER: Stops here if NOT called from IDLE state
        if only_same_direction: return None

        # Phase 2: Turnaround
        ud = self.up_down.get_max()
        if ud is not None:
            if delete: self.up_down.delete_max()
            return ud


        # Phase 3: Switch Direction (Auto-switch)
        dd = self.down_down.get_max()
        id_ = self.internal_down.get_max()
        if dd is not None or du is not None or id_ is not None:
            self.direction = Direction.DOWN
            return self._process_down_logic(delete, only_same_direction=False) # [only_same_direction] remains False
        
        return None

    def _process_down_logic(self, delete: bool, only_same_direction: bool):
        PRIO_INTERNAL, PRIO_EXTERNAL, PRIO_MISSED = 0, 1, 2

        id_ = self.internal_down.get_max()
        dd = self.down_down.get_max()
        ud = self.up_down.get_max()

        candidates = []
        # Phase 1: Standard DOWN requests
        if id_ is not None: candidates.append((id_, PRIO_INTERNAL))
        if dd is not None: candidates.append((dd, PRIO_EXTERNAL))
        if ud is not None and ud < self.current_floor:          # Check for 'Missed' requests (up_down < current_floor)
            candidates.append((ud, PRIO_MISSED))

        if candidates:
            # Sort by Floor (Descending), lowest Priority wins ties
            target, priority = max(candidates, key=lambda x: (x[0], -x[1]))
            if delete:
                if priority == PRIO_INTERNAL: self.internal_down.delete_max()
                elif priority == PRIO_EXTERNAL: self.down_down.delete_max()
                else: self.up_down.delete_max()  # PRIO_MISSED
            return target

        #! THE BARRIER: Stops here if NOT called from IDLE state
        if only_same_direction: return None

        # Phase 2: Turnaround
        du = self.down_up.get_min()
        if du is not None:
            if delete: self.down_up.delete_min()
            return du

        # Phase 3: Switch Direction (Auto-switch)
        uu = self.up_up.get_min()
        iu = self.internal_up.get_min()
        if uu is not None or ud is not None or iu is not None:
            self.direction = Direction.UP
            return self._process_up_logic(delete, only_same_direction=False) # [only_same_direction] remains False
        
        return None
    
#!---------------------------------------------------------------------------------------------
    # --- HELPERS FOR UI STATE MANAGER ---

    def has_requests_above(self, floor: int) -> bool:
        return any(
            val is not None and val > floor
            for val in (
                self.internal_up.get_max(),
                self.up_up.get_max(),
                self.up_down.get_max(),
                self.down_up.get_max(),
            )
        )


    def has_requests_below(self, floor: int) -> bool:
        return any(
            val is not None and val < floor
            for val in (
                self.internal_down.get_min(),
                self.down_down.get_min(),
                self.down_up.get_min(),
                self.up_down.get_min(),
            )
        )
