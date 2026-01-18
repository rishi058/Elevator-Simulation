from .direction import Direction
from .elevator_system import Elevator
import asyncio

# Collective Control Dispatch System
# Uses SCAN algorithm for each elevator and smart dispatching

STOP_TIME = 5  # Time penalty per stop (in seconds)

class CollectiveDispatchController:
    def __init__(self, total_floors: int = 10, total_elevators: int = 3):
        self.total_floors = total_floors   
        self.total_elevators = total_elevators
        self.elevators = [Elevator(id=i, total_floors=total_floors) for i in range(total_elevators)]
        self.running_tasks = []
               
        self.ws_manager = None  # WebSocket manager for broadcasting state
        self.prev_state = None  # Track previous state to prevent duplicate broadcasts
        
        # Dynamic request queue: {(floor, direction): {"id": elevator_id, "uuid": request_uuid, "cost": cost}}
        self.dynamic_requests_queue = {}

        # Set up state change callbacks for each elevator
        for elevator in self.elevators:
            elevator.on_state_change = self._on_elevator_state_change

    def set_websocket_manager(self, ws_manager):  
        self.ws_manager = ws_manager

    # ─────────────────────────────────────────────────────────────
    # ELEVATOR LIFECYCLE
    # ─────────────────────────────────────────────────────────────

    async def start(self): 
        # Run all elevators concurrently
        self.running_tasks = [asyncio.create_task(elevator.run()) for elevator in self.elevators] 

        # Start the dynamic optimizer task
        self.running_tasks.append(asyncio.create_task(self._run_dynamic_request_handler()))
        
        # Wait for all elevator tasks (they run forever)
        await asyncio.gather(*self.running_tasks, return_exceptions=True)

    async def stop(self): 
        for task in self.running_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for elevator in self.elevators:
            elevator.cleanup()
        
        self.elevators = []
        self.running_tasks = []
        self.dynamic_requests_queue = {}

    # ─────────────────────────────────────────────────────────────
    # ELEVATOR DISPATCH LOGIC (Collective Control)
    # ─────────────────────────────────────────────────────────────

    def add_request(self, floor: int, direction: str):
        """
        Calculates the best elevator, dispatches immediately, and tracks the UUID.
        """
        best_id, cost = self._get_best_elevator(floor, direction)   
        
        # Dispatch IMMEDIATELY to ensure the elevator starts moving.
        # Capture the UUID returned by StopScheduler for future reassignment.
        req_uuid = self.elevators[best_id].add_request(floor, direction)

        # Track in dynamic queue for potential reassignment
        self.dynamic_requests_queue[(floor, direction)] = {
            "id": best_id,
            "uuid": req_uuid,
            "cost": cost
        }
        return best_id

    def add_stop(self, id: int, floor: int):
        if id < 0 or id >= len(self.elevators):
            raise ValueError(f"Invalid elevator ID: {id}")
        
        self.elevators[id].add_stop(floor)

    def _select_elevator(self, floor: int, direction: str) -> Elevator:
        best_id, _ = self._get_best_elevator(floor, direction)
        return self.elevators[best_id]

    # ─────────────────────────────────────────────────────────────
    # ELEVATOR SELECTION COST CALCULATION
    # ─────────────────────────────────────────────────────────────

    def _get_best_elevator(self, floor: int, direction: str) -> tuple:
        """
        Calculate cost for each elevator and return (best_id, cost).
        """
        cost_info = []

        for elevator in self.elevators:
            cost = self._calculate_elevator_cost(elevator, floor, direction)
            cost_info.append((cost, elevator.id))

        # Sort by cost (lowest first)
        cost_info.sort(key=lambda x: x[0])
        
        return (cost_info[0][1], cost_info[0][0])  # (id, cost)

    def _calculate_elevator_cost(self, elevator: Elevator, floor: int, direction: str) -> float:
        """Calculate the cost for a specific elevator to serve a request."""
        curr_floor = int(elevator.current_floor)
        elev_dir = elevator.get_effective_direction()
        
        # Get elevator's scheduled stops info
        lowest_stop = self._get_lowest_stop(elevator)
        highest_stop = self._get_highest_stop(elevator)
        
        # IDLE: Simple distance
        if elev_dir == Direction.IDLE:
            return abs(floor - curr_floor)

        # Request wants UP
        if direction == Direction.UP:
            if elev_dir == Direction.UP:
                if curr_floor <= floor:
                    stops_between = self._count_stops_in_range(elevator, curr_floor, floor, Direction.UP)
                    return (floor - curr_floor) + STOP_TIME * stops_between
                else:
                    # Going UP but past the floor (Circle back)
                    if highest_stop is None: highest_stop = curr_floor
                    if lowest_stop is None: lowest_stop = curr_floor
                    
                    dist = (highest_stop - curr_floor) + \
                           (highest_stop - lowest_stop) + \
                           (floor - lowest_stop)
                    
                    total_stops = self._count_all_stops(elevator)
                    return dist + STOP_TIME * total_stops
            
            else:  # elev_dir == Direction.DOWN
                if lowest_stop is None: lowest_stop = curr_floor
                
                dist = (curr_floor - lowest_stop) + (floor - lowest_stop)
                stops_in_down = self._count_stops_in_range(elevator, lowest_stop, curr_floor, Direction.DOWN)
                stops_in_up = self._count_stops_in_range(elevator, lowest_stop, floor, Direction.UP)
                
                return dist + STOP_TIME * (stops_in_down + stops_in_up)

        # Request wants DOWN
        else:
            if elev_dir == Direction.DOWN:
                if curr_floor >= floor:
                    stops_between = self._count_stops_in_range(elevator, floor, curr_floor, Direction.DOWN)
                    return (curr_floor - floor) + STOP_TIME * stops_between
                else:
                    # Going DOWN but past the floor (Circle back)
                    if lowest_stop is None: lowest_stop = curr_floor
                    if highest_stop is None: highest_stop = curr_floor
                    
                    dist = (curr_floor - lowest_stop) + \
                           (highest_stop - lowest_stop) + \
                           (highest_stop - floor)
                    
                    total_stops = self._count_all_stops(elevator)
                    return dist + STOP_TIME * total_stops
            
            else:  # elev_dir == Direction.UP
                if highest_stop is None: highest_stop = curr_floor
                
                dist = (highest_stop - curr_floor) + (highest_stop - floor)
                stops_in_up = self._count_stops_in_range(elevator, curr_floor, highest_stop, Direction.UP)
                stops_in_down = self._count_stops_in_range(elevator, floor, highest_stop, Direction.DOWN)
                
                return dist + STOP_TIME * (stops_in_up + stops_in_down)

    # ─────────────────────────────────────────────────────────────
    # HEAP HELPERS (UPDATED FOR TUPLES)
    # ─────────────────────────────────────────────────────────────

    def _unpack_val(self, val_tuple):
        """Helper to safely extract floor int from (floor, uuid) tuple."""
        if val_tuple is None: return None
        if isinstance(val_tuple, (tuple, list)):
            return val_tuple[0]
        return val_tuple  # In case it's already an int (legacy safety)

    def _get_lowest_stop(self, elevator: Elevator) -> int | None:
        """Get the lowest scheduled stop floor."""
        candidates = []
        
        # MaxHeaps (store negated floors or special objects).
        # We use .get_min_value() which returns the actual lowest FLOOR INT
        if elevator.down_down.get_max() is not None:
            candidates.append(elevator.down_down.get_min_value())
        
        if elevator.internal_down.get_max() is not None:
            candidates.append(elevator.internal_down.get_min_value())

        if elevator.up_down.get_max() is not None:
            candidates.append(elevator.up_down.get_min_value())
            
        # MinHeaps: get_min() returns (floor, uuid). We need floor.
        if elevator.down_up.get_min() is not None:
            candidates.append(self._unpack_val(elevator.down_up.get_min()))
        
        return min(candidates) if candidates else None

    def _get_highest_stop(self, elevator: Elevator) -> int | None:
        """Get the highest scheduled stop floor."""
        candidates = []
        
        # MinHeaps (store positive floors).
        # We use .get_max_value() which returns the actual highest FLOOR INT
        if elevator.up_up.get_min() is not None:
            candidates.append(elevator.up_up.get_max_value())
            
        if elevator.internal_up.get_min() is not None:
            candidates.append(elevator.internal_up.get_max_value())

        # MinHeap
        if elevator.down_up.get_min() is not None:
            candidates.append(elevator.down_up.get_max_value())
        
        # MaxHeap: get_max() returns (floor, uuid). We need floor.
        if elevator.up_down.get_max() is not None:
            candidates.append(self._unpack_val(elevator.up_down.get_max()))
        
        return max(candidates) if candidates else None

    def _count_stops_in_range(self, elevator: Elevator, low: int, high: int, direction: str) -> int:
        count = 0
        if direction == Direction.UP:
            count += self._count_minheap_in_range(elevator.internal_up.heap, low, high)
            count += self._count_minheap_in_range(elevator.up_up.heap, low, high)
            count += self._count_minheap_in_range(elevator.down_up.heap, low, high)
        else:
            count += self._count_maxheap_in_range(elevator.internal_down.heap, low, high)
            count += self._count_maxheap_in_range(elevator.down_down.heap, low, high)
            count += self._count_maxheap_in_range(elevator.up_down.heap, low, high)
        return count

    def _count_minheap_in_range(self, heap: list, low: int, high: int) -> int:
        """Count elements in MinHeap [(floor, uuid), ...]"""
        # x is (floor, uuid), so x[0] is floor
        return sum(1 for x in heap if low <= x[0] <= high)

    def _count_maxheap_in_range(self, heap: list, low: int, high: int) -> int:
        """Count elements in MaxHeap [(-floor, uuid), ...]"""
        # x is (-floor, uuid), so -x[0] is floor
        return sum(1 for x in heap if low <= -x[0] <= high)

    def _count_all_stops(self, elevator: Elevator) -> int:
        return (
            len(elevator.internal_up.heap) +
            len(elevator.internal_down.heap) +
            len(elevator.up_up.heap) +
            len(elevator.up_down.heap) +
            len(elevator.down_down.heap) +
            len(elevator.down_up.heap)
        )

    # ─────────────────────────────────────────────────────────────
    # DYNAMIC REQUEST HANDLER
    # ─────────────────────────────────────────────────────────────

    async def _run_dynamic_request_handler(self):
        """
        Periodically re-evaluate request assignments.
        Uses remove_request to perform clean reassignment.
        """
        while True:
            try:
                # Use list(...) to iterate safely over keys while modifying dict
                for (floor, direction), info in list(self.dynamic_requests_queue.items()):
                    current_id = info["id"]
                    current_uuid = info["uuid"]
                    
                    # 1. Recalculate best elevator
                    best_id, new_cost = self._get_best_elevator(floor, direction)
                    
                    # 2. Get current elevator's cost for this request
                    current_cost = self._calculate_elevator_cost(
                        self.elevators[current_id], floor, direction
                    )

                    # 3. Clean up reached targets (Approximation logic)
                    if current_cost < 2: 
                        del self.dynamic_requests_queue[(floor, direction)]
                        continue

                    # 4. Attempt Reassignment
                    IMPROVEMENT_THRESHOLD = 5  # Only switch if we save significant time
                    
                    if best_id != current_id and (current_cost - new_cost) > IMPROVEMENT_THRESHOLD:
                        print(f"[Dynamic] Switching Floor {floor} {direction} from Elev {current_id} -> {best_id}")
                        
                        # Try to remove from the old elevator
                        removed = self.elevators[current_id].remove_request(current_uuid)
                        
                        if removed:
                            # Add to the new elevator
                            new_uuid = self.elevators[best_id].add_request(floor, direction)
                            
                            # Update tracking info
                            self.dynamic_requests_queue[(floor, direction)] = {
                                "id": best_id,
                                "uuid": new_uuid,
                                "cost": new_cost
                            }
                        else:
                            # If removal failed (request likely processed or door open), stop tracking
                            del self.dynamic_requests_queue[(floor, direction)]

            except Exception as e:
                print(f"[Dynamic Handler] Error: {e}")
            
            await asyncio.sleep(1)

    # ─────────────────────────────────────────────────────────────
    # STATUS & WEBSOCKET
    # ───────────────────────────────────────────────────────────── 
    
    def get_status(self) -> dict:
        return {
            "total_floors": self.total_floors,
            "total_elevators": self.total_elevators,
            "elevators": [
                elevator.get_status() for elevator in self.elevators
            ]
        }

    async def _on_elevator_state_change(self, elevator):
        await self._broadcast_state()

    async def _broadcast_state(self):
        if self.ws_manager is None:
            return

        try:
            loop = asyncio.get_running_loop()
            
            elevators_state = [
                elevator.get_status() for elevator in self.elevators
            ]
            
            current_state_key = str(elevators_state)
            if self.prev_state == current_state_key:
                return  
            
            self.prev_state = current_state_key
            
            state = {
                "type": "state_update",
                "total_floors": self.total_floors,
                "elevators": elevators_state,
                "timestamp": loop.time()
            }

            await self.ws_manager.broadcast(state)
        except Exception as e:
            print(f"[Controller] Error broadcasting state: {e}")