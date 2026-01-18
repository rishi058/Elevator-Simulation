from .direction import Direction
from .base_elevator import BaseElevator
from .heap import MinHeap, MaxHeap
import asyncio
import uuid

class StopScheduler(BaseElevator):    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        
        # All heaps now store (floor, uuid)
        self.internal_up = MinHeap()
        self.internal_down = MaxHeap()
        self.up_up = MinHeap()
        self.down_down = MaxHeap()
        self.up_down = MaxHeap()
        self.down_up = MinHeap()

    def add_request(self, input_floor: int, input_dir: str, request_uuid: str = None):
        """
        Returns the UUID of the request for tracking.
        """
        if request_uuid is None:
            request_uuid = str(uuid.uuid4())

        curr = self.current_floor
        eff_dir = self.get_effective_direction()
        
        # --- Logic matches original, but passes (floor, uuid) to heaps ---
        
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

    def remove_request(self, request_uuid: str):
        """
        Removes a request and returns (floor, direction) if found, else None.
        """
        # 1. Check UP_UP (Going UP, Want UP)
        f = self.up_up.remove_by_uuid(request_uuid)
        if f is not None: return (f, Direction.UP)
        
        # 2. Check DOWN_DOWN (Going DOWN, Want DOWN)
        f = self.down_down.remove_by_uuid(request_uuid)
        if f is not None: return (f, Direction.DOWN)
        
        # 3. Check UP_DOWN (Phase 2: Going UP, Want DOWN - Turnaround)
        # The request itself is DOWN, even if the car is currently moving UP to get there.
        f = self.up_down.remove_by_uuid(request_uuid)
        if f is not None: return (f, Direction.DOWN)

        # 4. Check DOWN_UP (Phase 2: Going DOWN, Want UP - Turnaround)
        # The request itself is UP.
        f = self.down_up.remove_by_uuid(request_uuid)
        if f is not None: return (f, Direction.UP)
        
        return None

    def add_stop(self, floor: int):
        # Internal stops (pressed inside car) usually don't need tracking UUIDs
        # We assign a dummy one or internal one if needed
        dummy_uuid = f"int_{floor}_{uuid.uuid4().hex[:4]}"
        
        if floor > self.current_floor:
            self.internal_up.insert(floor, dummy_uuid)
            if self.direction == Direction.IDLE: self.direction = Direction.UP
        elif floor < self.current_floor:
            self.internal_down.insert(floor, dummy_uuid)
            if self.direction == Direction.IDLE: self.direction = Direction.DOWN

    # --- HELPERS FOR UI STATE MANAGER ---
    # These abstract the tuple logic so UIStateManager doesn't need to know about UUIDs
    
    def _peek_floor(self, heap_val):
        """Extract just the floor integer from a (floor, uuid) tuple."""
        return heap_val[0] if heap_val else None

    def has_requests_above(self, floor: int) -> bool:
        """Check if any requests exist above the given floor."""
        # internal_up (MinHeap)
        if self.internal_up.get_max_value() is not None and self.internal_up.get_max_value() > floor: return True
        # up_up (MinHeap)
        if self.up_up.get_max_value() is not None and self.up_up.get_max_value() > floor: return True
        # up_down (MaxHeap) - Critical for Turnaround logic
        if self.up_down.get_max_value() is not None and self.up_down.get_max_value() > floor: return True
        # down_up (MinHeap) - Edge cases
        if self.down_up.get_max_value() is not None and self.down_up.get_max_value() > floor: return True

        return False

    def has_requests_below(self, floor: int) -> bool:
        """Check if any requests exist below the given floor."""
        # internal_down (MaxHeap)
        if self.internal_down.get_min_value() is not None and self.internal_down.get_min_value() < floor: return True
        # down_down (MaxHeap)
        if self.down_down.get_min_value() is not None and self.down_down.get_min_value() < floor: return True
        # down_up (MinHeap) - Critical for Turnaround logic
        if self.down_up.get_min_value() is not None and self.down_up.get_min_value() < floor: return True
        # up_down (MaxHeap) - Edge cases
        if self.up_down.get_min_value() is not None and self.up_down.get_min_value() < floor: return True
        
        return False

    # --- STOP SELECTION LOGIC ---

    def get_next_stop(self, delete: bool = True, only_same_direction: bool = False):
        """
        Retrieves the next floor (int). Unpacks the (floor, uuid) tuple.
        """
        # Helper to safely extract floor from tuple or return None
        def peek_floor(heap_tuple):
            return heap_tuple[0] if heap_tuple else None

        # Priority Constants
        PRIO_INTERNAL = 0
        PRIO_EXTERNAL = 1
        PRIO_MISSED = 2

        # --- IDLE LOGIC ---
        if self.direction == Direction.IDLE:
            up_target = peek_floor(self.up_up.get_min())
            down_target = peek_floor(self.down_down.get_max())
            up_turn = peek_floor(self.up_down.get_max())
            down_turn = peek_floor(self.down_up.get_min())

            if up_target is not None:
                if delete: self.up_up.extract_min()
                return up_target
            if down_target is not None:
                if delete: self.down_down.extract_max()
                return down_target
            if up_turn is not None:
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)
            if down_turn is not None:
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            return None

        # --- UP LOGIC ---
        if self.direction == Direction.UP:
            candidates = []

            # Unwrap tuples: (floor, uuid) -> Use floor for sorting
            if self.internal_up.get_min():
                candidates.append((self.internal_up.get_min()[0], PRIO_INTERNAL, 'internal_up'))
            if self.up_up.get_min():
                candidates.append((self.up_up.get_min()[0], PRIO_EXTERNAL, 'up_up'))
            
            du = self.down_up.get_min()
            if du and du[0] > self.current_floor:
                candidates.append((du[0], PRIO_MISSED, 'down_up'))

            if candidates:
                target_floor, _, source = min(candidates, key=lambda x: (x[0], x[1]))
                if delete:
                    if source == 'internal_up': self.internal_up.extract_min()
                    elif source == 'up_up': self.up_up.extract_min()
                    elif source == 'down_up': self.down_up.extract_min()
                return target_floor # Return INT

            if only_same_direction: return None

            # Turnaround
            target = self.up_down.get_max()
            if target:
                if delete: self.up_down.extract_max()
                return target[0] # Return INT

            # Switch Direction
            if (len(self.down_down) > 0 or len(self.down_up) > 0 or len(self.internal_down) > 0):
                self.direction = Direction.DOWN
                return self.get_next_stop(delete, only_same_direction)
            return None

        # --- DOWN LOGIC ---
        if self.direction == Direction.DOWN:
            candidates = []

            if self.internal_down.get_max():
                candidates.append((self.internal_down.get_max()[0], PRIO_INTERNAL, 'internal_down'))
            if self.down_down.get_max():
                candidates.append((self.down_down.get_max()[0], PRIO_EXTERNAL, 'down_down'))
            
            ud = self.up_down.get_max()
            if ud and ud[0] < self.current_floor:
                candidates.append((ud[0], PRIO_MISSED, 'up_down'))

            if candidates:
                # Custom Max key: Highest Floor, then Lowest Priority
                target_floor, _, source = max(candidates, key=lambda x: (x[0], -x[1]))
                if delete:
                    if source == 'internal_down': self.internal_down.extract_max()
                    elif source == 'down_down': self.down_down.extract_max()
                    elif source == 'up_down': self.up_down.extract_max()
                return target_floor

            if only_same_direction: return None

            target = self.down_up.get_min()
            if target:
                if delete: self.down_up.extract_min()
                return target[0]

            if (len(self.up_up) > 0 or len(self.up_down) > 0 or len(self.internal_up) > 0):
                self.direction = Direction.UP
                return self.get_next_stop(delete, only_same_direction)
            return None