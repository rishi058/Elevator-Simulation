from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio

class Elevator(UIStateManager):    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        self.on_state_change = None  # Callback for state change notifications
        self.prev_stop = None  # Track previous stop to avoid double door open
        #! (floor, direction) tracking for active movement
        self.active_request_target = None
        
    async def run(self):
        while True:
            self.update_ui_requests()
            self.sync_ui_state()  # Clean up any ghost values from race conditions

            stop, req_dir = self.get_next_stop()
            if stop is None:
                # Clean reset when IDLE
                self.direction = Direction.IDLE
                self.moving_direction = Direction.IDLE
                self.active_request_target = None # Reset active target
                await self._notify_state_change()
                await asyncio.sleep(1)
                continue  
            
            #! Set Active Target
            if req_dir is not None: self.active_request_target = (stop, req_dir)

            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self._notify_state_change()

            while self.is_door_open:
                await asyncio.sleep(1)
            
            # --- MOVE LOOP ---
            while self.current_floor != stop: 
                new_stop, new_req_dir = self.get_next_stop(delete=False)
                
                # Robust Interrupt Check
                if new_stop is not None:
                    interrupt = False
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        interrupt = True
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        interrupt = True
                
                    if interrupt:
                        self.get_next_stop(delete=True)
                        requeued_any = False # Robust Re-queueing
                        
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
                        if not requeued_any: self.add_stop(stop)
                        
                        stop = new_stop
                        #! Update Active Target
                        if new_req_dir: self.active_request_target = (stop, new_req_dir) 
                        await self._notify_state_change()

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self._notify_state_change()
                await asyncio.sleep(1)

            # --- ARRIVAL ---
            # Skip door open if we just stopped at this floor (handles external + internal same floor)
            if self.prev_stop == stop:
                self.prev_stop = None  # Reset to allow future stops at this floor
                continue
            
            self.prev_stop = stop
            
            self.is_door_open = True
            # Clear active target upon arrival
            self.active_request_target = None 
            self.moving_direction = self.direction            
            self.update_ui_requests() 
            await self._notify_state_change()
            await asyncio.sleep(5) 
            self.is_door_open = False
            await self._notify_state_change()

    # ─────────────────────────────────────────────────────────────
    # UI STATE SYNCHRONIZATION (Override)
    # ─────────────────────────────────────────────────────────────

    def sync_ui_state(self):
        """
        Override sync_ui_state to also check active_request_target.
        A floor should NOT be removed from UI if it's the current active target.
        """
        # Get active target info if exists
        active_floor = None
        active_dir = None
        if self.active_request_target is not None:
            active_floor, active_dir = self.active_request_target
        
        # Check UP requests - floor should exist in up_up, down_up, OR be the active target
        floors_to_remove_up = []
        for floor in self.ui_external_up_requests:
            # Skip if this floor is the active target with UP direction
            if active_floor == floor and active_dir == Direction.UP:
                continue
            if (self.up_up.find(floor) is None and 
                self.down_up.find(floor) is None):
                floors_to_remove_up.append(floor)
        
        for floor in floors_to_remove_up:
            self.ui_external_up_requests.discard(floor)
        
        # Check DOWN requests - floor should exist in down_down, up_down, OR be the active target
        floors_to_remove_down = []
        for floor in self.ui_external_down_requests:
            # Skip if this floor is the active target with DOWN direction
            if active_floor == floor and active_dir == Direction.DOWN:
                continue
            if (self.down_down.find(floor) is None and 
                self.up_down.find(floor) is None):
                floors_to_remove_down.append(floor)
        
        for floor in floors_to_remove_down:
            self.ui_external_down_requests.discard(floor)

    # ─────────────────────────────────────────────────────────────
    # STATUS & WEBSOCKET
    # ───────────────────────────────────────────────────────────── 
    
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
    
    # ─────────────────────────────────────────────────────────────
    # COST CALCULATION HELPERS
    # ─────────────────────────────────────────────────────────────

    def is_request_active(self, floor: int, direction: str) -> bool:
        """Checks if the elevator already has this exact floor in its schedule."""
        if self.active_request_target == (floor, direction): return True
        
        if direction == Direction.UP:
            if self.up_up.find(floor) is not None: return True
            if self.down_up.find(floor) is not None: return True
        else:
            if self.down_down.find(floor) is not None: return True
            if self.up_down.find(floor) is not None: return True
        return False

    def get_lowest_stop(self) -> int | None:
        candidates = []

        if self.active_request_target is not None:
            candidates.append(self.active_request_target[0])

        uu = self.up_up.get_min()[0]
        if uu is not None: candidates.append(uu)

        dd = self.down_down.get_min()[0]
        if dd is not None: candidates.append(dd)

        id_ = self.internal_down.get_min()[0]
        if id_ is not None: candidates.append(id_)

        iu = self.internal_up.get_min()[0]
        if iu is not None: candidates.append(iu)

        ud = self.up_down.get_min()[0]
        if ud is not None: candidates.append(ud)
        
        du = self.down_up.get_min()[0]
        if du is not None: candidates.append(du)

        return min(candidates) if candidates else None

    def get_highest_stop(self) -> int | None:
        candidates = []

        if self.active_request_target is not None:
            candidates.append(self.active_request_target[0])

        uu = self.up_up.get_max()[0]
        if uu is not None: candidates.append(uu)

        dd = self.down_down.get_max()[0]
        if dd is not None: candidates.append(dd)

        id_ = self.internal_down.get_max()[0]
        if id_ is not None: candidates.append(id_)

        iu = self.internal_up.get_max()[0]
        if iu is not None: candidates.append(iu)

        ud = self.up_down.get_max()[0]
        if ud is not None: candidates.append(ud)

        du = self.down_up.get_max()[0]
        if du is not None: candidates.append(du)

        return max(candidates) if candidates else None

    def count_stops_in_range(self, low: int, high: int, direction: str) -> int:
        count = 0

        if direction == Direction.UP:
            count += self.internal_up.count_nodes_in_range(low, high)
            count += self.up_up.count_nodes_in_range(low, high)
            count += self.up_down.count_nodes_in_range(low, high) # up_down stops are hit in TURN-AROUND
        else:
            count += self.internal_down.count_nodes_in_range(low, high)
            count += self.down_down.count_nodes_in_range(low, high)
            count += self.down_up.count_nodes_in_range(low, high) # down_up stops are hit in TURN-AROUND
    
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
        