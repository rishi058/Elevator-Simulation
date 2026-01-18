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
        # Phase 1: Main Sweep (e.g., Going UP, picking up UP requests)
        self.up_up = MinHeap()     # [Floor > Curr] Want UP
        self.down_down = MaxHeap() # [Floor < Curr] Want DOWN
        
        # Phase 2: Secondary Sweep (e.g., Going UP, picking up DOWN requests at top)
        self.up_down = MaxHeap()   # [Floor > Curr] Want DOWN
        self.down_up = MinHeap()   # [Floor < Curr] Want UP

    def add_request(self, input_floor: int, input_dir: str):
        """Sorts external requests into the correct Phase queue"""
        curr = self.current_floor
        eff_dir = self.get_effective_direction()
        
        # If IDLE, assign based on simple proximity/direction
        if eff_dir == Direction.IDLE:
            if input_floor > curr:
                self.up_up.insert(input_floor)
                self.direction = Direction.UP
            elif input_floor < curr:
                self.down_down.insert(input_floor)
                self.direction = Direction.DOWN
            else:
                if not self.is_door_open: asyncio.create_task(self.open_door())
            return

        # LOGIC MAP: Decide which queue this request belongs to
        if eff_dir == Direction.UP:
            if input_floor >= curr:
                if input_dir == Direction.UP: 
                    self.up_up.insert(input_floor)   # Standard: On our way
                else: 
                    self.up_down.insert(input_floor) # Turnaround: Pick up on way down
            else:
                self.down_up.insert(input_floor)     # Missed: Behind us (Phase 4)

        elif eff_dir == Direction.DOWN:
            if input_floor <= curr:
                if input_dir == Direction.DOWN: 
                    self.down_down.insert(input_floor) # Standard: On our way
                else: 
                    self.down_up.insert(input_floor)   # Turnaround: Pick up on way up
            else:
                self.up_down.insert(input_floor)       # Missed: Behind us (Phase 4)

    def add_stop(self, floor: int):
        """Internal car buttons always go to internal heaps"""
        if floor > self.current_floor:
            self.internal_up.insert(floor)
            if self.direction == Direction.IDLE:
                self.direction = Direction.UP
        elif floor < self.current_floor:
            self.internal_down.insert(floor)
            if self.direction == Direction.IDLE:
                self.direction = Direction.DOWN

    def get_next_stop(self, delete: bool = True, only_same_direction: bool = False):
        """
        Determines the next floor to visit.
        FIX: Explicitly checks 'is not None' to handle Floor 0 correctly.
        """
        # IDLE: Logic remains same
        if self.direction == Direction.IDLE:
            target = self.up_up.get_min() if self.up_up.get_min() is not None else self.down_down.get_max()
            # Note: The original 'or' logic there was also risky if up_up had 0, 
            # but up_up usually has floors > current.
            
            if target is not None:
                if delete:
                    if target == self.up_up.get_min(): self.up_up.extract_min()
                    else: self.down_down.extract_max()
                return target
            return None

        # --- UPWARD LOGIC ---
        if self.direction == Direction.UP:
            # Phase 1: Check Internal, Same-Direction, AND "Misplaced" Turnaround requests
            candidates = []

            # 1. Internal Requests
            if self.internal_up.get_min() is not None:
                candidates.append((self.internal_up.get_min(), 'internal_up'))
            
            # 2. Standard UP Requests
            if self.up_up.get_min() is not None:
                candidates.append((self.up_up.get_min(), 'up_up'))

            # 3. FALLBACK: Check 'down_up'
            du_val = self.down_up.get_min()
            if du_val is not None and du_val > self.current_floor:
                candidates.append((du_val, 'down_up'))

            # Select the Closest Target
            if candidates:
                target, source = min(candidates, key=lambda x: x[0])
                if delete:
                    if source == 'internal_up': self.internal_up.extract_min()
                    elif source == 'up_up': self.up_up.extract_min()
                    elif source == 'down_up': self.down_up.extract_min()
                return target
            
            if only_same_direction:
                return None

            # Phase 2: Turnaround Requests (Going UP but want DOWN)
            target = self.up_down.get_max()
            if target is not None:
                if delete: self.up_down.extract_max()
                return target

            # Phase 3: Switch Direction (THE FIX IS HERE)
            # We must check 'is not None' because Floor 0 evaluates to False
            if (self.down_down.get_max() is not None or 
                self.down_up.get_min() is not None or 
                self.internal_down.get_max() is not None):
                
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            
            return None

        # --- DOWNWARD LOGIC ---
        if self.direction == Direction.DOWN:
            # Phase 1: Check Internal, Same-Direction, AND "Misplaced" Turnaround requests
            candidates = []

            # 1. Internal Requests
            if self.internal_down.get_max() is not None:
                candidates.append((self.internal_down.get_max(), 'internal_down'))
            
            # 2. Standard DOWN Requests
            if self.down_down.get_max() is not None:
                candidates.append((self.down_down.get_max(), 'down_down'))

            # 3. FALLBACK: Check 'up_down'
            ud_val = self.up_down.get_max()
            if ud_val is not None and ud_val < self.current_floor:
                candidates.append((ud_val, 'up_down'))

            # Select the Closest Target
            if candidates:
                target, source = max(candidates, key=lambda x: x[0])
                if delete:
                    if source == 'internal_down': self.internal_down.extract_max()
                    elif source == 'down_down': self.down_down.extract_max()
                    elif source == 'up_down': self.up_down.extract_max()
                return target

            if only_same_direction:
                return None

            # Phase 2: Turnaround Requests (Going DOWN but want UP)
            target = self.down_up.get_min()
            if target is not None:
                if delete: self.down_up.extract_min()
                return target

            # Phase 3: Switch Direction (THE FIX IS HERE)
            if (self.up_up.get_min() is not None or 
                self.up_down.get_max() is not None or 
                self.internal_up.get_min() is not None):
                
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)

            return None