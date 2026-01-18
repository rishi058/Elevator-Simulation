from .direction import Direction
from .elevator_system import Elevator
import asyncio

# Collective Control Dispatch System
STOP_TIME = 5         # Seconds penalty per stop
TRAVEL_TIME = 5       # Seconds to move one floor
TURN_AROUND_PENALTY = 500  # Heavy penalty (seconds) to discourage switching direction mid-trip

class CollectiveDispatchController:
    def __init__(self, total_floors: int = 10, total_elevators: int = 3):
        self.total_floors = total_floors   
        self.total_elevators = total_elevators
        self.elevators = [Elevator(id=i, total_floors=total_floors) for i in range(total_elevators)]
        self.running_tasks = []
                
        self.ws_manager = None 
        self.prev_state = None 
        self.dynamic_requests_queue = {}

        for elevator in self.elevators:
            elevator.on_state_change = self._on_elevator_state_change

    def set_websocket_manager(self, ws_manager):  
        self.ws_manager = ws_manager

    # ─────────────────────────────────────────────────────────────
    # ELEVATOR LIFECYCLE
    # ─────────────────────────────────────────────────────────────

    async def start(self): 
        self.running_tasks = [asyncio.create_task(elevator.run()) for elevator in self.elevators] 
        self.running_tasks.append(asyncio.create_task(self._run_dynamic_request_handler()))
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
    # ELEVATOR DISPATCH LOGIC
    # ─────────────────────────────────────────────────────────────

    def add_request(self, floor: int, direction: str):
        best_id, cost = self._get_best_elevator(floor, direction)   
        
        req_uuid = self.elevators[best_id].add_request(floor, direction)

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
    # COST CALCULATION (FIXED)
    # ─────────────────────────────────────────────────────────────

    def _get_best_elevator(self, floor: int, direction: str) -> tuple:
        # Returns (best_id, cost)
        # Using simple min with key
        best_elev = min(
            self.elevators, 
            key=lambda e: self._calculate_elevator_cost(e, floor, direction)
        )
        return (best_elev.id, self._calculate_elevator_cost(best_elev, floor, direction))

    def _calculate_elevator_cost(self, elevator: Elevator, floor: int, direction: str) -> float:
        # 1. Prevent duplicate assignment
        if elevator.is_request_already_assigned(floor, direction):
            return float('inf')

        curr_floor = int(elevator.current_floor)
        elev_dir = elevator.get_effective_direction()
        
        # 2. Fix: Check direction instead of .state attribute
        is_moving_at_floor = (elev_dir != Direction.IDLE and curr_floor == floor)

        # 3. Get extremes (default to current floor if empty)
        lowest_stop = elevator.get_lowest_stop()
        highest_stop = elevator.get_highest_stop()
        
        if lowest_stop is None: lowest_stop = curr_floor
        if highest_stop is None: highest_stop = curr_floor

        # --- COST LOGIC ---
        
        # IDLE: Simple distance * Time
        if elev_dir == Direction.IDLE:
            return abs(floor - curr_floor) * TRAVEL_TIME

        # Request wants UP
        if direction == Direction.UP:
            if elev_dir == Direction.UP:
                # Normal: Elevator is below target
                if curr_floor <= floor and not is_moving_at_floor:
                    stops_between = elevator.count_stops_in_range(curr_floor, floor, Direction.UP)
                    return (floor - curr_floor) * TRAVEL_TIME + STOP_TIME * stops_between
                
                # Passed Target: Must go Top -> Turn -> Bottom -> Turn -> Target
                else:
                    turn_point = max(highest_stop, curr_floor)
                    # Dist: (curr -> turn) + (turn -> floor)
                    dist = (turn_point - curr_floor) + (turn_point - floor)
                    total_stops = elevator.get_total_stop_count()
                    return dist * TRAVEL_TIME + STOP_TIME * total_stops + TURN_AROUND_PENALTY
            
            else:  # elev_dir == Direction.DOWN
                # Turning Point at bottom is min of (Lowest Scheduled, Target Floor)
                turn_point = min(lowest_stop, floor)
                
                dist = (curr_floor - turn_point) + (floor - turn_point)
                stops_in_down = elevator.count_stops_in_range(turn_point, curr_floor, Direction.DOWN)
                stops_in_up = elevator.count_stops_in_range(turn_point, floor, Direction.UP)
                
                # Penalty applied because we are relying on it turning around
                return dist * TRAVEL_TIME + STOP_TIME * (stops_in_down + stops_in_up) + TURN_AROUND_PENALTY

        # Request wants DOWN
        else:
            if elev_dir == Direction.DOWN:
                # Normal: Elevator is above target
                if curr_floor >= floor and not is_moving_at_floor:
                    stops_between = elevator.count_stops_in_range(floor, curr_floor, Direction.DOWN)
                    return (curr_floor - floor) * TRAVEL_TIME + STOP_TIME * stops_between
                
                # Passed Target: Must go Bottom -> Turn -> Top -> Turn -> Target
                else:
                    turn_point = min(lowest_stop, curr_floor)
                    dist = (curr_floor - turn_point) + (floor - turn_point)
                    total_stops = elevator.get_total_stop_count()
                    return dist * TRAVEL_TIME + STOP_TIME * total_stops + TURN_AROUND_PENALTY
            
            else:  # elev_dir == Direction.UP
                turn_point = max(highest_stop, floor)
                
                dist = (turn_point - curr_floor) + (turn_point - floor)
                stops_in_up = elevator.count_stops_in_range(curr_floor, turn_point, Direction.UP)
                stops_in_down = elevator.count_stops_in_range(floor, turn_point, Direction.DOWN)
                
                return dist * TRAVEL_TIME + STOP_TIME * (stops_in_up + stops_in_down) + TURN_AROUND_PENALTY

    # ─────────────────────────────────────────────────────────────
    # DYNAMIC REQUEST HANDLER
    # ─────────────────────────────────────────────────────────────

    async def _run_dynamic_request_handler(self):
        while True:
            try:
                for (floor, direction), info in list(self.dynamic_requests_queue.items()):
                    current_id = info["id"]
                    current_uuid = info["uuid"]
                    
                    best_id, new_cost = self._get_best_elevator(floor, direction)
                    current_cost = self._calculate_elevator_cost(self.elevators[current_id], floor, direction)

                    # 10s = 2 floors. If closer than that, don't reassign
                    if current_cost < 10: 
                        del self.dynamic_requests_queue[(floor, direction)]
                        continue

                    IMPROVEMENT_THRESHOLD = 5 # 5 seconds
                    if best_id != current_id and (current_cost - new_cost) > IMPROVEMENT_THRESHOLD:
                        removed = self.elevators[current_id].remove_request(current_uuid)
                        if removed:
                            new_uuid = self.elevators[best_id].add_request(floor, direction)
                            self.dynamic_requests_queue[(floor, direction)] = {
                                "id": best_id, "uuid": new_uuid, "cost": new_cost
                            }
                        else:
                            del self.dynamic_requests_queue[(floor, direction)]
            except Exception as e:
                print(f"[Dynamic Handler] Error: {e}")
            await asyncio.sleep(0.5)

    # ─────────────────────────────────────────────────────────────
    # STATUS & WEBSOCKET
    # ───────────────────────────────────────────────────────────── 
    
    def get_status(self) -> dict:
        return {
            "total_floors": self.total_floors,
            "total_elevators": self.total_elevators,
            "elevators": [elevator.get_status() for elevator in self.elevators]
        }

    async def _on_elevator_state_change(self, elevator):
        await self._broadcast_state()

    async def _broadcast_state(self):
        if self.ws_manager is None: return
        try:
            loop = asyncio.get_running_loop()
            elevators_state = [elevator.get_status() for elevator in self.elevators]
            current_state_key = str(elevators_state)
            if self.prev_state == current_state_key: return  
            self.prev_state = current_state_key
            
            state = {
                "type": "state_update", "total_floors": self.total_floors,
                "elevators": elevators_state, "timestamp": loop.time()
            }
            await self.ws_manager.broadcast(state)
        except Exception:
            pass