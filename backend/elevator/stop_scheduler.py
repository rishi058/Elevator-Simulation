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

    def add_request(self, input_floor: int, input_dir: str):
        curr = self.current_floor
        eff_dir = self.get_effective_direction()
        
        # FIX: Even if IDLE, check Direction to sort into Turnaround queues
        if eff_dir == Direction.IDLE:
            if input_floor > curr:
                if input_dir == Direction.UP:
                    self.up_up.insert(input_floor)
                else:
                    self.up_down.insert(input_floor) # 2D goes here!
                self.direction = Direction.UP
            elif input_floor < curr:
                if input_dir == Direction.DOWN:
                    self.down_down.insert(input_floor)
                else:
                    self.down_up.insert(input_floor)
                self.direction = Direction.DOWN
            else:
                if not self.is_door_open: asyncio.create_task(self.open_door())
            return

        # Standard Logic
        if eff_dir == Direction.UP:
            if input_floor >= curr:
                if input_dir == Direction.UP: 
                    self.up_up.insert(input_floor)
                else: 
                    self.up_down.insert(input_floor)
            else:
                self.down_up.insert(input_floor)

        elif eff_dir == Direction.DOWN:
            if input_floor <= curr:
                if input_dir == Direction.DOWN: 
                    self.down_down.insert(input_floor)
                else: 
                    self.down_up.insert(input_floor)
            else:
                self.up_down.insert(input_floor)

    def add_stop(self, floor: int):
        if floor > self.current_floor:
            self.internal_up.insert(floor)
            if self.direction == Direction.IDLE: self.direction = Direction.UP
        elif floor < self.current_floor:
            self.internal_down.insert(floor)
            if self.direction == Direction.IDLE: self.direction = Direction.DOWN

    def get_next_stop(self, delete: bool = True, only_same_direction: bool = False):
        # IDLE: Check all queues
        if self.direction == Direction.IDLE:
            up_target = self.up_up.get_min()
            down_target = self.down_down.get_max()
            up_turnaround = self.up_down.get_max()
            down_turnaround = self.down_up.get_min()

            if up_target is not None:
                if delete: self.up_up.extract_min()
                return up_target
            if down_target is not None:
                if delete: self.down_down.extract_max()
                return down_target
            # Handle Turnaround starts from IDLE
            if up_turnaround is not None:
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)
            if down_turnaround is not None:
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            return None

        # UP LOGIC
        if self.direction == Direction.UP:
            candidates = []
            if self.internal_up.get_min() is not None:
                candidates.append((self.internal_up.get_min(), 'internal_up'))
            if self.up_up.get_min() is not None:
                candidates.append((self.up_up.get_min(), 'up_up'))
            
            # Fallback for "Missed" requests below us
            du_val = self.down_up.get_min()
            if du_val is not None and du_val > self.current_floor:
                candidates.append((du_val, 'down_up'))

            if candidates:
                target, source = min(candidates, key=lambda x: x[0])
                if delete:
                    if source == 'internal_up': self.internal_up.extract_min()
                    elif source == 'up_up': self.up_up.extract_min()
                    elif source == 'down_up': self.down_up.extract_min()
                return target
            
            if only_same_direction: return None

            # Phase 2: Turnaround
            target = self.up_down.get_max()
            if target is not None:
                if delete: self.up_down.extract_max()
                return target

            # Phase 3: Switch Direction (The original Fix)
            if (self.down_down.get_max() is not None or 
                self.down_up.get_min() is not None or 
                self.internal_down.get_max() is not None):
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            return None

        # DOWN LOGIC
        if self.direction == Direction.DOWN:
            candidates = []
            if self.internal_down.get_max() is not None:
                candidates.append((self.internal_down.get_max(), 'internal_down'))
            if self.down_down.get_max() is not None:
                candidates.append((self.down_down.get_max(), 'down_down'))
            
            ud_val = self.up_down.get_max()
            if ud_val is not None and ud_val < self.current_floor:
                candidates.append((ud_val, 'up_down'))

            if candidates:
                target, source = max(candidates, key=lambda x: x[0])
                if delete:
                    if source == 'internal_down': self.internal_down.extract_max()
                    elif source == 'down_down': self.down_down.extract_max()
                    elif source == 'up_down': self.up_down.extract_max()
                return target

            if only_same_direction: return None

            target = self.down_up.get_min()
            if target is not None:
                if delete: self.down_up.extract_min()
                return target

            if (self.up_up.get_min() is not None or 
                self.up_down.get_max() is not None or 
                self.internal_up.get_min() is not None):
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)
            return None