# Fix Ghost Value Bug in UI External Buttons

## Problem Description

The UI external buttons (hall call buttons) have a "ghost value" issue where:
- **Ghost buttons stay ON**: Hall lights remain illuminated after all scheduler trees are empty

### Root Cause Analysis (Updated)

The bug is a **race condition** between two async processes:

1. **Elevator's [run()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/elevator_system.py#13-96) loop**: Calls [get_next_stop(delete=True)](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/stop_scheduler.py#91-135) which removes the request UUID from the AVL tree
2. **Dynamic handler's [_run_dynamic_request_handler()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/multi_elevator_system.py#223-252)**: Calls [remove_request(uuid)](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/stop_scheduler.py#66-86) which tries to find and remove by UUID

**Race condition sequence:**
```
T1: Elevator.run() -> get_next_stop(delete=True) -> Removes UUID from tree
T2: Dynamic handler -> remove_request(uuid) -> Can't find UUID (already gone!) -> Returns None
T3: UIStateManager.remove_request() receives None -> Returns False, UI NOT cleared
T4: Ghost value remains in ui_external_down_requests
```

The [remove_request](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/stop_scheduler.py#66-86) function relies on finding the UUID in the scheduler trees. When [get_next_stop](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/stop_scheduler.py#91-135) has already deleted the request, the UUID no longer exists, and UI state is never cleared.

---

## Proposed Changes

### Core Solution: Validate UI State Against Scheduler Trees

Add a `sync_ui_state()` method that ensures UI sets only contain floors that are actually present in the scheduler trees.

#### [MODIFY] [ui_state_manager.py](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py)

Add a new method that synchronizes UI state with actual scheduler state:

```python
def sync_ui_state(self):
    """
    Synchronize UI state with scheduler trees.
    Remove any floors from UI sets that are no longer in any scheduler tree.
    This prevents ghost values from race conditions.
    """
    # Check UP requests
    floors_to_remove_up = []
    for floor in self.ui_external_up_requests:
        # Check if this floor exists in any UP-related tree
        if (self.up_up.find(floor) is None and 
            self.down_up.find(floor) is None):
            floors_to_remove_up.append(floor)
    
    for floor in floors_to_remove_up:
        self.ui_external_up_requests.discard(floor)
    
    # Check DOWN requests  
    floors_to_remove_down = []
    for floor in self.ui_external_down_requests:
        # Check if this floor exists in any DOWN-related tree
        if (self.down_down.find(floor) is None and 
            self.up_down.find(floor) is None):
            floors_to_remove_down.append(floor)
    
    for floor in floors_to_remove_down:
        self.ui_external_down_requests.discard(floor)
```

#### [MODIFY] [elevator_system.py](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/elevator_system.py)

Call `sync_ui_state()` in the main run loop to periodically clean up stale UI state:

```python
async def run(self):
    while True:
        self.update_ui_requests()
        self.sync_ui_state()  # Add this line to clean up ghost values
        # ... rest of the loop
```

---

## Verification Plan

### Automated Tests

Run the ghost value test:

```bash
cd d:\STUDY\Web-Dev\Elevator_Problem\multi-elevator-system
python -m tests.ghost_value_test
```

**Expected outcome:**
- All 3 random permutations should complete with NO ghost button bugs
- Final summary: `"Permutations with ghost button bugs: 0"`

---
---
---
---
---

# Ghost Value Bug Fix - Walkthrough

## Summary

Fixed the ghost value bug in UI external buttons (hall lights) where buttons would remain lit after requests were fulfilled.

## Root Cause

**Race condition** between two async processes:

1. `Elevator.run()` calls [get_next_stop(delete=True)](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/stop_scheduler.py#91-135) → removes request UUID from AVL tree
2. [_run_dynamic_request_handler()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/multi_elevator_system.py#223-252) calls [remove_request(uuid)](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py#32-49) → can't find UUID (already deleted) → returns `None` → UI NOT cleared

## Changes Made

### [ui_state_manager.py](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py)

Added [sync_ui_state()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py#85-110) method that validates UI sets against scheduler trees:

```diff:ui_state_manager.py
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
===
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
```

---

### [elevator_system.py](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/elevator_system.py)

1. Added call to [sync_ui_state()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py#85-110) in main run loop
2. Override [sync_ui_state()](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/backend/elevator/ui_state_manager.py#85-110) to also check `active_request_target` (prevents removing UI for requests currently in-transit):

```diff:elevator_system.py
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
        
===
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
        
```

---

### [ghost_value_test.py](file:///d:/STUDY/Web-Dev/Elevator_Problem/multi-elevator-system/tests/ghost_value_test.py)

Fixed test to wait for all elevators to be IDLE before checking for ghost values:

```diff:ghost_value_test.py
import asyncio
import sys
import os
import itertools

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from backend.elevator.multi_elevator_system import CollectiveDispatchController
from backend.elevator.direction import Direction

class CostLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("tests/cost_log.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure flush

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = CostLogger()

class HallButtonLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("tests/hall_button_log.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure flush

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = HallButtonLogger()

def print_tree(tree):
    nodes = []
    def traverse(node):
        if not node: return
        traverse(node.left)
        nodes.append(node.key)
        traverse(node.right)
    traverse(tree.root)
    return nodes

def get_hall_button_state(controller):
    """Get current hall button state for all elevators"""
    state = {}
    for i, elev in enumerate(controller.elevators):
        state[f"E{i}"] = {
            "floor": elev.current_floor,
            "direction": str(elev.direction),
            "ui_up": list(elev.ui_external_up_requests),
            "ui_down": list(elev.ui_external_down_requests),
            "ui_internal": list(elev.ui_internal_requests)
        }
    return state

async def run_single_permutation(perm_index, requests):
    """Run a single permutation test and return if bug was found"""
    print(f"\n{'='*60}")
    print(f"PERMUTATION {perm_index}: {requests}")
    print(f"{'='*60}")
    
    controller = CollectiveDispatchController(total_floors=7, total_elevators=3)
    
    # Start controller in a background task
    start_task = asyncio.create_task(controller.start())

    # Give it a moment to initialize
    await asyncio.sleep(1)

    print("Adding requests...")
    for floor, direction in requests:
        aid = controller.add_request(floor, direction)
        print(f"Requesting: {floor} {direction} -> Assigned to E{aid}")

    print("Requests added. Waiting for elevators to handle them...")

    # Wait for completion (simulation)
    timeout = 120  # seconds
    start_time = asyncio.get_event_loop().time()
    second_counter = 0
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        # Log hall button state each second
        second_counter += 1
        hall_state = get_hall_button_state(controller)
        print(f"\n[Second {second_counter}] Hall Button State:")
        for elev_id, state in hall_state.items():
            print(f"  {elev_id}: Floor={state['floor']}, Dir={state['direction']}, "
                  f"UP={state['ui_up']}, DOWN={state['ui_down']}, INT={state['ui_internal']}")
        
        # Check if all 6 trees are empty for all elevators
        all_trees_empty = True
        for elev in controller.elevators:
            trees = [
                elev.up_up, elev.down_down,
                elev.up_down, elev.down_up,
                elev.internal_up, elev.internal_down
            ]
            for tree in trees:
                if tree.root is not None:
                    all_trees_empty = False
                    break
            if not all_trees_empty:
                break
        
        if all_trees_empty and elapsed > 5:
            print("\n*** All 6 scheduler trees are empty for all elevators ***")
            break
        
        if elapsed > timeout:
            print("Timeout waiting for trees to empty")
            break
            
        await asyncio.sleep(1)

    print("\n--- Simulation Finished (or Timed out) ---")
    print("Checking for lingering requests and internal scheduler state...")
    
    found_bug = False
    
    for i, elev in enumerate(controller.elevators):
        # Access UIStateManager state directly
        up_reqs = elev.ui_external_up_requests
        down_reqs = elev.ui_external_down_requests
        internal_reqs = elev.ui_internal_requests
        
        print(f"\n[Elevator {i}]")
        print(f"  Current Floor: {elev.current_floor}")
        print(f"  Direction: {elev.direction}")
        print(f"  UI External UP: {up_reqs}")
        print(f"  UI External DOWN: {down_reqs}")
        print(f"  UI Internal: {internal_reqs}")
        
        # Check Scheduler Trees
        print(f"  Scheduler up_up: {print_tree(elev.up_up)}")
        print(f"  Scheduler down_down: {print_tree(elev.down_down)}")
        print(f"  Scheduler up_down: {print_tree(elev.up_down)}")
        print(f"  Scheduler down_up: {print_tree(elev.down_up)}")
        print(f"  Scheduler internal_up: {print_tree(elev.internal_up)}")
        print(f"  Scheduler internal_down: {print_tree(elev.internal_down)}")

        if up_reqs or down_reqs or internal_reqs:
            print(f"  -> HAS LINGERING REQUESTS (GHOST BUTTON)")
            found_bug = True
            
    if found_bug:
        print("\nBUG REPRODUCED: Some buttons stayed ON (ghost button state).")
    else:
        print("\nNo bug found. All requests cleared.")

    controller.stop()
    return found_bug

async def main():
    import random
    
    print("Starting Ghost Value Test with Random Permutations...")
    print("This will test 3 random permutations to find ghost button states.\n")
    
    # Base requests to permute
    base_requests = [
        (6, Direction.DOWN),
        (5, Direction.UP),
        (5, Direction.DOWN),
        (4, Direction.UP),
        (4, Direction.DOWN),
        (3, Direction.UP),
        (3, Direction.DOWN)
    ]
    
    # Generate all permutations and pick 3 random ones
    all_permutations = list(itertools.permutations(base_requests))
    total_perms = len(all_permutations)
    print(f"Total permutations available: {total_perms}")
    
    # Pick 3 random permutations
    selected_perms = random.sample(all_permutations, 3)
    print(f"Selected 3 random permutations for testing.\n")
    
    # Track which permutations found bugs
    buggy_permutations = []
    
    for idx, perm in enumerate(selected_perms):
        perm_list = list(perm)
        found_bug = await run_single_permutation(idx + 1, perm_list)
        
        if found_bug:
            buggy_permutations.append((idx + 1, perm_list))
    
    # Final Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total permutations tested: 3")
    print(f"Permutations with ghost button bugs: {len(buggy_permutations)}")
    
    if buggy_permutations:
        print("\nBuggy permutations:")
        for perm_idx, perm_reqs in buggy_permutations:
            print(f"  Permutation {perm_idx}: {perm_reqs}")
    else:
        print("\nNo ghost button bugs found in any permutation!")

if __name__ == "__main__":
    asyncio.run(main())
===
import asyncio
import sys
import os
import itertools

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from backend.elevator.multi_elevator_system import CollectiveDispatchController
from backend.elevator.direction import Direction

class CostLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("tests/cost_log.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure flush

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = CostLogger()

class HallButtonLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("tests/hall_button_log.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure flush

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = HallButtonLogger()

def print_tree(tree):
    nodes = []
    def traverse(node):
        if not node: return
        traverse(node.left)
        nodes.append(node.key)
        traverse(node.right)
    traverse(tree.root)
    return nodes

def get_hall_button_state(controller):
    """Get current hall button state for all elevators"""
    state = {}
    for i, elev in enumerate(controller.elevators):
        state[f"E{i}"] = {
            "floor": elev.current_floor,
            "direction": str(elev.direction),
            "ui_up": list(elev.ui_external_up_requests),
            "ui_down": list(elev.ui_external_down_requests),
            "ui_internal": list(elev.ui_internal_requests)
        }
    return state

async def run_single_permutation(perm_index, requests):
    """Run a single permutation test and return if bug was found"""
    print(f"\n{'='*60}")
    print(f"PERMUTATION {perm_index}: {requests}")
    print(f"{'='*60}")
    
    controller = CollectiveDispatchController(total_floors=7, total_elevators=3)
    
    # Start controller in a background task
    start_task = asyncio.create_task(controller.start())

    # Give it a moment to initialize
    await asyncio.sleep(1)

    print("Adding requests...")
    for floor, direction in requests:
        aid = controller.add_request(floor, direction)
        print(f"Requesting: {floor} {direction} -> Assigned to E{aid}")

    print("Requests added. Waiting for elevators to handle them...")

    # Wait for completion (simulation)
    timeout = 120  # seconds
    start_time = asyncio.get_event_loop().time()
    second_counter = 0
    
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        # Log hall button state each second
        second_counter += 1
        hall_state = get_hall_button_state(controller)
        print(f"\n[Second {second_counter}] Hall Button State:")
        for elev_id, state in hall_state.items():
            print(f"  {elev_id}: Floor={state['floor']}, Dir={state['direction']}, "
                  f"UP={state['ui_up']}, DOWN={state['ui_down']}, INT={state['ui_internal']}")
        
        # Check if all 6 trees are empty for all elevators AND all elevators are IDLE
        all_trees_empty = True
        all_elevators_idle = True
        for elev in controller.elevators:
            # Check if elevator is still moving (not IDLE)
            if elev.direction != Direction.IDLE:
                all_elevators_idle = False
            
            trees = [
                elev.up_up, elev.down_down,
                elev.up_down, elev.down_up,
                elev.internal_up, elev.internal_down
            ]
            for tree in trees:
                if tree.root is not None:
                    all_trees_empty = False
                    break
            if not all_trees_empty:
                break
        
        # Only finish when ALL trees are empty AND ALL elevators are IDLE
        if all_trees_empty and all_elevators_idle and elapsed > 5:
            print("\n*** All 6 scheduler trees are empty AND all elevators IDLE ***")
            break
        
        if elapsed > timeout:
            print("Timeout waiting for trees to empty")
            break
            
        await asyncio.sleep(1)

    print("\n--- Simulation Finished (or Timed out) ---")
    print("Checking for lingering requests and internal scheduler state...")
    
    found_bug = False
    
    for i, elev in enumerate(controller.elevators):
        # Access UIStateManager state directly
        up_reqs = elev.ui_external_up_requests
        down_reqs = elev.ui_external_down_requests
        internal_reqs = elev.ui_internal_requests
        
        print(f"\n[Elevator {i}]")
        print(f"  Current Floor: {elev.current_floor}")
        print(f"  Direction: {elev.direction}")
        print(f"  UI External UP: {up_reqs}")
        print(f"  UI External DOWN: {down_reqs}")
        print(f"  UI Internal: {internal_reqs}")
        
        # Check Scheduler Trees
        print(f"  Scheduler up_up: {print_tree(elev.up_up)}")
        print(f"  Scheduler down_down: {print_tree(elev.down_down)}")
        print(f"  Scheduler up_down: {print_tree(elev.up_down)}")
        print(f"  Scheduler down_up: {print_tree(elev.down_up)}")
        print(f"  Scheduler internal_up: {print_tree(elev.internal_up)}")
        print(f"  Scheduler internal_down: {print_tree(elev.internal_down)}")

        if up_reqs or down_reqs or internal_reqs:
            print(f"  -> HAS LINGERING REQUESTS (GHOST BUTTON)")
            found_bug = True
            
    if found_bug:
        print("\nBUG REPRODUCED: Some buttons stayed ON (ghost button state).")
    else:
        print("\nNo bug found. All requests cleared.")

    controller.stop()
    return found_bug

async def main():
    import random
    
    print("Starting Ghost Value Test with Random Permutations...")
    print("This will test 3 random permutations to find ghost button states.\n")
    
    # Base requests to permute
    base_requests = [
        (6, Direction.DOWN),
        (5, Direction.UP),
        (5, Direction.DOWN),
        (4, Direction.UP),
        (4, Direction.DOWN),
        (3, Direction.UP),
        (3, Direction.DOWN)
    ]
    
    # Generate all permutations and pick 3 random ones
    all_permutations = list(itertools.permutations(base_requests))
    total_perms = len(all_permutations)
    print(f"Total permutations available: {total_perms}")
    
    # Pick 3 random permutations
    selected_perms = random.sample(all_permutations, 3)
    print(f"Selected 3 random permutations for testing.\n")
    
    # Track which permutations found bugs
    buggy_permutations = []
    
    for idx, perm in enumerate(selected_perms):
        perm_list = list(perm)
        found_bug = await run_single_permutation(idx + 1, perm_list)
        
        if found_bug:
            buggy_permutations.append((idx + 1, perm_list))
    
    # Final Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total permutations tested: 3")
    print(f"Permutations with ghost button bugs: {len(buggy_permutations)}")
    
    if buggy_permutations:
        print("\nBuggy permutations:")
        for perm_idx, perm_reqs in buggy_permutations:
            print(f"  Permutation {perm_idx}: {perm_reqs}")
    else:
        print("\nNo ghost button bugs found in any permutation!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Verification

Test results show **0 ghost button bugs** across all 3 random permutations:

```
FINAL SUMMARY
================================================================================
Total permutations tested: 3
Permutations with ghost button bugs: 0

No ghost button bugs found in any permutation!
```
