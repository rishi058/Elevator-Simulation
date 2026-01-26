from .direction import Direction
from .elevator_system import Elevator
import asyncio

# Collective Control Dispatch System
STOP_TIME = 5         # Seconds penalty per stop
TRAVEL_TIME = 5       # Seconds to move one floor
TURNAROUND_PENALTY = 30 # total_floors/2 * TRAVEL_TIME 

class CollectiveDispatchController:
    def __init__(self, total_floors: int = 10, total_elevators: int = 3):
        self.total_floors = total_floors   
        self.total_elevators = total_elevators
        self.elevators = [Elevator(id=i, total_floors=total_floors) for i in range(total_elevators)]
        self.running_tasks = []
                
        self.ws_manager = None 
        self.prev_state = None 
        #! Key: (floor, direction), Value: {"id": elevator_id, "uuid": request_uuid}
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
        # Here, We can check if the request is already assigned to an elevator
        # If yes, then we can return the elevator id
        # If no, then we can assign the request to the best elevator
        if (floor, direction) in self.dynamic_requests_queue:
            return self.dynamic_requests_queue[(floor, direction)]["id"]
            
        # Check if any elevator is already handling this request (redundancy check)
        for elevator in self.elevators:
            # A elevator has a active request, only when the elevator will fullfill it within 5s.
            if elevator.is_request_active(floor, direction):
                print("OK")
                return elevator.id
        
        best_id, cost = self._get_best_elevator(floor, direction)   
        
        req_uuid = self.elevators[best_id].add_request(floor, direction)

        self.dynamic_requests_queue[(floor, direction)] = {
            "id": best_id,
            "uuid": req_uuid,
        }

        return best_id

    def add_stop(self, id: int, floor: int):
        self.elevators[id].add_stop(floor)

    # ─────────────────────────────────────────────────────────────
    # COST CALCULATION (FIXED)
    # ─────────────────────────────────────────────────────────────

    # This function is called N-times every 0.5s (where N is number of requests in queue)

    def _get_best_elevator(self, floor: int, direction: str) -> tuple:  # Returns (best_id, cost)
        costs = []

        for elevator in self.elevators:
            elevator_cost = self._calculate_elevator_cost(elevator, floor, direction)
            costs.append((elevator.id, elevator_cost))
            
        costs = sorted(costs, key=lambda x: x[1])

        # I am seeing that i am not getting updated costs here...
        for c in costs:
            print(f"E{c[0]+1}: {c[1]}",  end=", ")
        print()  

        return (costs[0][0], costs[0][1]) # best_id, best_cost

    #!----------------------------------------------------------------------------------------------
    
    # This function is called N * M times every 0.5s (where N is number of requests in queue & M is number of elevators)
    
    def _calculate_elevator_cost(self, elevator: Elevator, req_floor: int, req_dir: str) -> float:
        elev_pos = elevator.current_floor
        elev_dir = elevator.get_effective_direction() 

        # IDLE: Simple distance * Time 
        if elev_dir == Direction.IDLE:
            return abs(req_floor - elev_pos) * TRAVEL_TIME    
        
        # 3. Get extremes (default to current req_floor if empty)
        lowest_stop = elevator.get_lowest_stop()
        highest_stop = elevator.get_highest_stop()
        
        if lowest_stop is None: lowest_stop = elev_pos
        if highest_stop is None: highest_stop = elev_pos

        # Ensure bounds include current position to prevent negative costs
        lowest_stop = min(lowest_stop, elev_pos)
        highest_stop = max(highest_stop, elev_pos)

        # Request wants UP
        if req_dir == Direction.UP:
            if elev_dir == Direction.UP:
                # Normal: Elevator is below target
                if elev_pos <= req_floor:
                    stops_count = elevator.count_stops_in_range(elev_pos, req_floor, Direction.UP)
                    # Exclude req_floor from stop penalty if it's already a stop
                    x = elevator.count_stops_in_range(req_floor, req_floor, Direction.UP)
                    y = elevator.count_stops_in_range(req_floor, req_floor, Direction.DOWN)
                    is_dest_stop = (x + y) > 0
                    if is_dest_stop: stops_count -= 1
                    
                    return (req_floor - elev_pos) * TRAVEL_TIME + (STOP_TIME * stops_count)
                
                # Passed Target: Must go Top -> Turn -> Bottom -> Turn -> Target
                else: 
                    # Dist: (curr -> turn) + (turn -> bottom) + (bottom -> req_floor)
                    # Edge case : req_floor < lowest_stop 
                    dist = (highest_stop - elev_pos) + (highest_stop - lowest_stop) + abs(req_floor - lowest_stop)
                    total_stops = elevator.get_total_stop_count()
                    return (dist * TRAVEL_TIME) + (STOP_TIME * total_stops) + TURNAROUND_PENALTY
            
            else:  # elev_dir == Direction.DOWN
                # Must go curr -> Bottom -> Turn -> req_floor
                # Dist: (curr -> bottom) + (bottom -> req_floor)

                turn_point = min(lowest_stop, req_floor)

                dist = (elev_pos - turn_point) + (req_floor - turn_point)
                stops_in_down = elevator.count_stops_in_range(turn_point, elev_pos, Direction.DOWN)
                stops_in_up = elevator.count_stops_in_range(turn_point, req_floor, Direction.UP)
                
                # Penalty applied because we are relying on it turning around
                penalty = 0 if turn_point == req_floor else TURNAROUND_PENALTY
                
                stops_cost = (stops_in_down + stops_in_up) * STOP_TIME
                # Check if turn_point (req_floor) is counted as a stop
                x = elevator.count_stops_in_range(req_floor, req_floor, Direction.UP)
                y = elevator.count_stops_in_range(req_floor, req_floor, Direction.DOWN)
                is_turn_point_stop = (x + y) > 0
                if is_turn_point_stop: stops_cost -= STOP_TIME

                return (dist * TRAVEL_TIME) + stops_cost + penalty

        # Request wants DOWN
        else:
            if elev_dir == Direction.DOWN: 
                # Normal: Elevator is above target
                if elev_pos >= req_floor:
                    stops_count = elevator.count_stops_in_range(req_floor, elev_pos, Direction.DOWN)
                    # Exclude req_floor from stop penalty if it's already a stop
                    x = elevator.count_stops_in_range(req_floor, req_floor, Direction.UP)
                    y = elevator.count_stops_in_range(req_floor, req_floor, Direction.DOWN)
                    is_dest_stop = (x + y) > 0
                    if is_dest_stop: stops_count -= 1
                    return (elev_pos - req_floor) * TRAVEL_TIME + (STOP_TIME * stops_count)
                
                # Passed Target: Must go Bottom -> Turn -> Top -> Turn -> Target 
                # Edge case : req_floor > highest_stop
                else:
                    dist = (elev_pos - lowest_stop) + (highest_stop - lowest_stop) + abs(highest_stop - req_floor)
                    total_stops = elevator.get_total_stop_count()
                    return (dist * TRAVEL_TIME) + (STOP_TIME * total_stops) + TURNAROUND_PENALTY
            
            else:  # elev_dir == Direction.UP
                if highest_stop <= req_floor:
                    # Optimization: Elevator will finish its UP tasks below the target,
                    # so it can continue UP to req_floor and turn there.
                    stops_in_range = elevator.count_stops_in_range(elev_pos, req_floor, Direction.UP)
                    dist = req_floor - elev_pos
                    return (dist * TRAVEL_TIME) + (STOP_TIME * stops_in_range)

                turn_point = max(highest_stop, req_floor)
                
                dist = (turn_point - elev_pos) + (turn_point - req_floor)
                stops_in_up = elevator.count_stops_in_range(elev_pos, turn_point, Direction.UP)
                stops_in_down = elevator.count_stops_in_range(req_floor, turn_point, Direction.DOWN)
                
                penalty = 0 if turn_point == req_floor else TURNAROUND_PENALTY

                stops_cost = (stops_in_up + stops_in_down) * STOP_TIME
                # Check if turn_point (req_floor) is counted as a stop
                x = elevator.count_stops_in_range(req_floor, req_floor, Direction.UP)
                y = elevator.count_stops_in_range(req_floor, req_floor, Direction.DOWN)
                is_turn_point_stop = (x + y) > 0
                if is_turn_point_stop: stops_cost -= STOP_TIME

                return (dist * TRAVEL_TIME) + stops_cost + penalty


    # ─────────────────────────────────────────────────────────────
    # DYNAMIC REQUEST HANDLER
    # ─────────────────────────────────────────────────────────────

    async def _run_dynamic_request_handler(self):
        while True:
            try:
                for (floor, direction), info in list(self.dynamic_requests_queue.items()):
                    print(f"{floor}{direction} == ", end="")

                    current_id = info["id"]
                    current_uuid = info["uuid"]
                    
                    best_id, new_cost = self._get_best_elevator(floor, direction)
                    current_cost = self._calculate_elevator_cost(self.elevators[current_id], floor, direction)

                    # Don't reassign
                    if current_cost <= 5: 
                        del self.dynamic_requests_queue[(floor, direction)]
                        continue

                    IMPROVEMENT_THRESHOLD = 5 # 5 seconds 
                    if best_id != current_id and (current_cost - new_cost) > IMPROVEMENT_THRESHOLD:
                        print(f"[Re-Assigning Elevator] Request:{floor}{direction}, Old:E{current_id+1}, New:E{best_id+1}")
                        removed = self.elevators[current_id].remove_request(current_uuid)
                        if removed:
                            new_uuid = self.elevators[best_id].add_request(floor, direction)
                            self.dynamic_requests_queue[(floor, direction)] = {"id": best_id, "uuid": new_uuid}
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

    #! elevator param is neccessary...
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