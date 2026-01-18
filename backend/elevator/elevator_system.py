from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio, copy

class Elevator(UIStateManager):    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        self.on_state_change = None  # Callback for state change notifications
        
    async def run(self):
        while True:
            self.update_ui_requests()

            stop = self.get_next_stop()
            if stop is None:
                # Clean reset when IDLE
                self.direction = Direction.IDLE
                self.moving_direction = Direction.IDLE
                await self._notify_state_change()
                await asyncio.sleep(1)
                continue  
            
            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self._notify_state_change()

            while self.is_door_open:
                await asyncio.sleep(1)
            
            # --- MOVE LOOP ---
            while self.current_floor != stop: 
                new_stop = self.get_next_stop(delete=False, only_same_direction=True)
                interrupt = False
                
                # Robust Interrupt Check
                if new_stop is not None:
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        interrupt = True
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        interrupt = True
                
                if interrupt:
                    self.get_next_stop(delete=True, only_same_direction=True)
                    
                    # Robust Re-queueing
                    requeued_any = False
                    
                    if stop in self.ui_internal_requests:
                        self.add_stop(stop)
                        requeued_any = True
                    
                    if stop in self.ui_external_down_requests:
                        self.add_request(stop, Direction.DOWN)
                        requeued_any = True
                        
                    if stop in self.ui_external_up_requests:
                        self.add_request(stop, Direction.UP)
                        requeued_any = True
                    
                    # Fallback: If not found in UI sets (rare), default to Internal
                    if not requeued_any:
                        self.add_stop(stop)
                    
                    stop = new_stop
                    await self._notify_state_change()

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self._notify_state_change()
                await asyncio.sleep(1)

            # --- ARRIVAL ---
            self.is_door_open = True
            self.moving_direction = self.direction            
            self.update_ui_requests() 
            await self._notify_state_change()
            await asyncio.sleep(5) 
            self.is_door_open = False
            await self._notify_state_change()


    #!---------------------------------------------------------------------------------
    
    async def _notify_state_change(self): # Notify Controller about state change
        if self.on_state_change:
            await self.on_state_change(self)
    
    def get_status(self) -> dict:
        return {
            "elevator_id": self.id,
            "current_floor": self.current_floor,
            "direction": self.get_effective_direction(),
            "is_door_open": self.is_door_open,
            "external_up_requests": list(self.ui_external_up_requests),
            "external_down_requests": list(self.ui_external_down_requests),
            "internal_requests": list(self.ui_internal_requests),
        }
    
    #!---------------------------------------------------------------------------------
    
    # ─────────────────────────────────────────────────────────────
    # COST CALCULATION HELPERS
    # ─────────────────────────────────────────────────────────────

    def is_request_already_assigned(self, floor: int, direction: str) -> bool:
        """Checks if the elevator already has this exact floor in its schedule."""
        # Helper to check if floor exists in the internal heap list
        def in_min_heap(heap, val): return any(item[0] == val for item in heap.heap)
        def in_max_heap(heap, val): return any(-item[0] == val for item in heap.heap)

        if direction == Direction.UP:
            if in_min_heap(self.up_up, floor): return True
            if in_min_heap(self.down_up, floor): return True
            if in_min_heap(self.internal_up, floor): return True
        else:
            if in_max_heap(self.down_down, floor): return True
            if in_max_heap(self.up_down, floor): return True
            if in_max_heap(self.internal_down, floor): return True
        return False

    def get_lowest_stop(self) -> int | None:
        candidates = []
        if self.down_down.get_max() is not None: candidates.append(self.down_down.get_min_value())
        if self.internal_down.get_max() is not None: candidates.append(self.internal_down.get_min_value())
        if self.up_down.get_max() is not None: candidates.append(self.up_down.get_min_value())
        
        # down_up is MinHeap. get_min() returns (floor, uuid)
        dup = self.down_up.get_min()
        if dup is not None: candidates.append(dup[0])
        
        return min(candidates) if candidates else None

    def get_highest_stop(self) -> int | None:
        candidates = []
        if self.up_up.get_min() is not None: candidates.append(self.up_up.get_max_value())
        if self.internal_up.get_min() is not None: candidates.append(self.internal_up.get_max_value())
        if self.down_up.get_min() is not None: candidates.append(self.down_up.get_max_value())
        
        # up_down is MaxHeap. get_max() returns (floor, uuid)
        ud = self.up_down.get_max()
        if ud is not None: candidates.append(ud[0])
        
        return max(candidates) if candidates else None

    def count_stops_in_range(self, low: int, high: int, direction: str) -> int:
        count = 0
        def count_min(heap, l, h): return sum(1 for x in heap.heap if l <= x[0] <= h)
        def count_max(heap, l, h): return sum(1 for x in heap.heap if l <= -x[0] <= h)

        if direction == Direction.UP:
            count += count_min(self.internal_up, low, high)
            count += count_min(self.up_up, low, high)
            count += count_min(self.down_up, low, high)
        else:
            count += count_max(self.internal_down, low, high)
            count += count_max(self.down_down, low, high)
            count += count_max(self.up_down, low, high)
        return count

    def get_total_stop_count(self) -> int:
        return (len(self.internal_up) + len(self.internal_down) +
                len(self.up_up) + len(self.up_down) +
                len(self.down_down) + len(self.down_up))

    #!---------------------------------------------------------------------------------

    def cleanup(self):
        """Clean up elevator resources"""
        self.id = None
        self.total_floors = None
        self.current_floor = None  
        self.direction = None
        self.is_door_open = None
        self.moving_direction = None
        #----------------------------------------
        self.up_up = None
        self.down_down = None
        self.up_down = None
        self.down_up = None
        self.internal_up = None
        self.internal_down = None
        #----------------------------------------
        self.ui_external_up_requests = None
        self.ui_external_down_requests = None
        self.ui_internal_requests = None
        #----------------------------------------
        self.on_state_change = None
        