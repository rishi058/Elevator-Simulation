from .direction import Direction
from .base_elevator import BaseElevator
from .heap import MinHeap, MaxHeap
import asyncio

class StopScheduler(BaseElevator):    
    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        
        # --- Internal Requests (Car Buttons) ---
        self.internal_up = MinHeap()
        self.internal_down = MaxHeap()

        # --- External Requests (Hall Buttons) ---
        self.up_up = MinHeap()     # [Phase 1] Going UP, want UP
        self.down_down = MaxHeap() # [Phase 1] Going DOWN, want DOWN
        
        self.up_down = MaxHeap()   # [Phase 2] Going UP, want DOWN (Turnaround)
        self.down_up = MinHeap()   # [Phase 2] Going DOWN, want UP (Turnaround)

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

    def get_next_stop(self, delete: bool = True, only_same_direction: bool = True):
        # Priority Constants (Lower is better)
        PRIO_INTERNAL, PRIO_EXTERNAL, PRIO_MISSED = 0, 1, 2
        uu, dd = self.up_up.get_min(), self.down_down.get_max()
        ud, du = self.up_down.get_max(), self.down_up.get_min()  # Missed requests
        iu, id_ = self.internal_up.get_min(), self.internal_down.get_max() # Internal requests

        # --- IDLE LOGIC ---
        if self.direction == Direction.IDLE:
            # Phase 1: Pick the first available Same-Direction target
            if uu is not None: 
                self.direction = Direction.UP
                if delete: self.up_up.extract_min()
                return uu
            
            if dd is not None: 
                self.direction = Direction.DOWN
                if delete: self.down_down.extract_max()
                return dd

            # Phase 2: Handle Turnarounds (The Critical Fix)
            # CRITICAL: Pass False here. We must allow the logic to see the 'up_down' queue (which is normally blocked by the flag).
            if ud is not None: 
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction=False)
            # CRITICAL: Pass False here.
            if du is not None: 
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction=False)
            
            return None

        # --- UP LOGIC ---
        if self.direction == Direction.UP:
            candidates = []
            # Phase 1: Standard UP requests
            if iu is not None: candidates.append((iu, PRIO_INTERNAL, 'internal_up'))
            if uu is not None: candidates.append((uu, PRIO_EXTERNAL, 'up_up'))
            # Check for 'Missed' requests (down_up > current_floor)
            if du is not None and du > self.current_floor: candidates.append((du, PRIO_MISSED, 'down_up'))

            if candidates:
                # Sort by Floor (Ascending), then Priority
                target, _, src = min(candidates, key=lambda x: (x[0], x[1]))
                if delete: self.internal_up.extract_min() if src == 'internal_up' else self.up_up.extract_min() if src == 'up_up' else self.down_up.extract_min()
                return target
            
            #! THE BARRIER: Stops here if called externally (Preserves your IDLE reset logic)
            if only_same_direction: return None

            # Phase 2: Turnaround (Only reachable if passed False from IDLE)
            if ud is not None:
                if delete: self.up_down.extract_max()
                return ud

            # Phase 3: Switch Direction (Auto-switch)
            # Note: This is rarely reached if your external loop resets on None, but kept for logical completeness.
            if dd is not None or du is not None or id_ is not None:
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            
            return None

        # --- DOWN LOGIC ---
        if self.direction == Direction.DOWN:
            candidates = []
            # Phase 1: Standard DOWN requests
            if id_ is not None: candidates.append((id_, PRIO_INTERNAL, 'internal_down'))
            if dd is not None: candidates.append((dd, PRIO_EXTERNAL, 'down_down'))
            # Check for 'Missed' requests (up_down < current_floor)
            if ud is not None and ud < self.current_floor: candidates.append((ud, PRIO_MISSED, 'up_down'))

            if candidates:
                # Sort by Floor (Descending for Max), lowest Priority wins ties.
                # We use key (floor, -priority) because max() compares element 0 then 1.
                target, _, src = max(candidates, key=lambda x: (x[0], -x[1]))
                if delete: self.internal_down.extract_max() if src == 'internal_down' else self.down_down.extract_max() if src == 'down_down' else self.up_down.extract_max()
                return target

            #! THE BARRIER: Stops here if called externally (Preserves your IDLE reset logic)
            if only_same_direction: return None

            # Phase 2: Turnaround (Only reachable if passed False from IDLE)
            if du is not None:
                if delete: self.down_up.extract_min()
                return du
            
            # Phase 3: Switch Direction (Auto-switch)
            if uu is not None or ud is not None or iu is not None:
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)
            
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
