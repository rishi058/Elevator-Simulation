from .direction import Direction
from .base_elevator import BaseElevator
from .avl_tree import AVLTree
import asyncio

class StopScheduler(BaseElevator):    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        self.internal_up = AVLTree()
        self.internal_down = AVLTree()
        self.up_up = AVLTree()
        self.down_down = AVLTree()
        self.up_down = AVLTree()
        self.down_up = AVLTree()

#!----------------------------------------------------------------------------------------------------

    def add_request(self, input_floor: int, input_dir: str, request_uuid: str):
        curr = self.current_floor
        eff_dir = self.get_effective_direction()
        
        # IDLE
        if eff_dir == Direction.IDLE:
            if input_floor > curr:
                if input_dir == Direction.UP: self.up_up.insert(input_floor, request_uuid)
                else: self.up_down.insert(input_floor, request_uuid)
                self.direction = Direction.UP
            elif input_floor < curr:
                if input_dir == Direction.DOWN: self.down_down.insert(input_floor, request_uuid)
                else: self.down_up.insert(input_floor, request_uuid)
                self.direction = Direction.DOWN
            else:
                if not self.is_door_open: asyncio.create_task(self.open_door())
            return request_uuid

        # MOVING UP
        if eff_dir == Direction.UP:
            if input_floor >= curr:
                if input_dir == Direction.UP: self.up_up.insert(input_floor, request_uuid)
                else: self.up_down.insert(input_floor, request_uuid)
            else:
                self.down_up.insert(input_floor, request_uuid) # Missed/Turnaround

        # MOVING DOWN
        elif eff_dir == Direction.DOWN:
            if input_floor <= curr:
                if input_dir == Direction.DOWN: self.down_down.insert(input_floor, request_uuid)
                else: self.down_up.insert(input_floor, request_uuid)
            else:
                self.up_down.insert(input_floor, request_uuid) # Missed/Turnaround
        
        return request_uuid
    
#!----------------------------------------------------------------------------------------------------

    def add_stop(self, floor: int, dummy_uuid: str):
        if floor > self.current_floor:
            self.internal_up.insert(floor, dummy_uuid)
            if self.direction == Direction.IDLE: self.direction = Direction.UP
        elif floor < self.current_floor:
            self.internal_down.insert(floor, dummy_uuid)
            if self.direction == Direction.IDLE: self.direction = Direction.DOWN

#!----------------------------------------------------------------------------------------------------

    def remove_request(self, request_uuid: str):
        # 1. Check UP_UP (Going UP, Want UP)
        f = self.up_up.delete_by_id(request_uuid)
        if f is not None: return (f, Direction.UP)
        
        # 2. Check DOWN_DOWN (Going DOWN, Want DOWN)
        f = self.down_down.delete_by_id(request_uuid)
        if f is not None: return (f, Direction.DOWN)
        
        # 3. Check UP_DOWN (Phase 2: Going UP, Want DOWN - Turnaround)
        # The request itself is DOWN, even if the car is currently moving UP to get there.
        f = self.up_down.delete_by_id(request_uuid)
        if f is not None: return (f, Direction.DOWN)

        # 4. Check DOWN_UP (Phase 2: Going DOWN, Want UP - Turnaround)
        # The request itself is UP.
        f = self.down_up.delete_by_id(request_uuid)
        if f is not None: return (f, Direction.UP)
        
        return None

#!----------------------------------------------------------------------------------------------------

    # external RUN loop likely relies on the function returning None to trigger state changes (like going to IDLE)

    def get_next_stop(self, delete:bool = True):
        # --- IDLE LOGIC ---
        if self.direction == Direction.IDLE:
            
            # 1. Check for ANY motivation to go UP (Internal OR External)
            iu = self.internal_up.get_min()[0]
            uu = self.up_up.get_min()[0]

            if iu is not None or uu is not None:
                self.direction = Direction.UP
                # We call the helper to ensure we pick the closest stop (Priority 0 vs 1)
                return self._process_up_logic(delete, only_same_direction=False)
            
            # 2. Check for ANY motivation to go DOWN (Internal OR External)
            id_ = self.internal_down.get_max()[0]
            dd = self.down_down.get_max()[0]
  
            if id_ is not None or dd is not None:
                self.direction = Direction.DOWN
                # We call the helper to ensure we pick the closest stop
                return self._process_down_logic(delete, only_same_direction=False)


            # Phase 2: Handle Turnarounds
            ud = self.up_down.get_max()[0]
            if ud is not None:
                self.direction = Direction.UP
                return self._process_up_logic(delete, only_same_direction=False)
            
            du = self.down_up.get_min()[0]
            if du is not None:
                self.direction = Direction.DOWN
                return self._process_down_logic(delete, only_same_direction=False)
            
            return None, None

        # --- ACTIVE LOGIC ---
        if self.direction == Direction.UP:
            return self._process_up_logic(delete, only_same_direction=True)
        
        if self.direction == Direction.DOWN:
            return self._process_down_logic(delete, only_same_direction=True)
        
        return None, None

    def _process_up_logic(self, delete: bool, only_same_direction: bool):
        PRIO_INTERNAL, PRIO_EXTERNAL, PRIO_MISSED = 0, 1, 2

        iu = self.internal_up.get_min()[0]
        uu = self.up_up.get_min()[0]
        du = self.down_up.get_min()[0]

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
            return target, Direction.UP

        #! THE BARRIER: Stops here if NOT called from IDLE state
        if only_same_direction: return None, None

        # Phase 2: Turnaround
        ud = self.up_down.get_max()[0]
        if ud is not None:
            if delete: self.up_down.delete_max()
            return ud, Direction.DOWN # Request wants DOWN


        # Phase 3: Switch Direction (Auto-switch)
        dd = self.down_down.get_max()[0]
        id_ = self.internal_down.get_max()[0]
        if dd is not None or du is not None or id_ is not None:
            self.direction = Direction.DOWN
            return self._process_down_logic(delete, only_same_direction=False) # [only_same_direction] remains False
        
        return None, None

    def _process_down_logic(self, delete: bool, only_same_direction: bool):
        PRIO_INTERNAL, PRIO_EXTERNAL, PRIO_MISSED = 0, 1, 2

        id_ = self.internal_down.get_max()[0]
        dd = self.down_down.get_max()[0]
        ud = self.up_down.get_max()[0]

        candidates = []
        # Phase 1: Standard DOWN requests
        if id_ is not None: candidates.append((id_, PRIO_INTERNAL))
        if dd is not None: candidates.append((dd, PRIO_EXTERNAL))
        if ud is not None and ud < self.current_floor:          # Check for 'Missed' requests (up_down < current_floor)
            candidates.append((ud, PRIO_MISSED)) # Wanting to go DOWN.

        if candidates:
            # Sort by Floor (Descending), lowest Priority wins ties
            target, priority = max(candidates, key=lambda x: (x[0], -x[1]))
            if delete:
                if priority == PRIO_INTERNAL: self.internal_down.delete_max()
                elif priority == PRIO_EXTERNAL: self.down_down.delete_max()
                else: self.up_down.delete_max()  # PRIO_MISSED
            return target, Direction.DOWN 

        #! THE BARRIER: Stops here if NOT called from IDLE state
        if only_same_direction: return None, None

        # Phase 2: Turnaround
        du = self.down_up.get_min()[0]
        if du is not None:
            if delete: self.down_up.delete_min()
            return du, Direction.UP # Request wants UP

        # Phase 3: Switch Direction (Auto-switch)
        uu = self.up_up.get_min()[0]
        iu = self.internal_up.get_min()[0]
        if uu is not None or ud is not None or iu is not None:
            self.direction = Direction.UP
            return self._process_up_logic(delete, only_same_direction=False) # [only_same_direction] remains False
        
        return None, None

#!---------------------------------------------------------------------------------------------
    # --- HELPERS FOR UI STATE MANAGER ---

    def has_requests_above(self, floor: int) -> bool:
        return any(
            val is not None and val > floor
            for val in (
                self.internal_up.get_max()[0],
                self.up_up.get_max()[0],
                self.up_down.get_max()[0],
                self.down_up.get_max()[0],
            )
        )


    def has_requests_below(self, floor: int) -> bool:
        return any(
            val is not None and val < floor
            for val in (
                self.internal_down.get_min()[0],
                self.down_down.get_min()[0],
                self.down_up.get_min()[0],
                self.up_down.get_min()[0],
            )
        )
