from .direction import Direction
from .elevator_system import Elevator
import asyncio

# Collective Control Dispatch System
# Uses SCAN algorithm for each elevator and smart dispatching

class CollectiveDispatchController:
    def __init__(self, total_floors: int = 10, total_elevators: int = 3):
        self.total_floors = total_floors   #! Only used for validation in fast-api
        self.total_elevators = total_elevators
        self.elevators = [Elevator(elevator_id=i, total_floors=total_floors) for i in range(total_elevators)]
        self.running_tasks = []
               
        self.ws_manager = None  # WebSocket manager for broadcasting state
        self.prev_state = None  # Track previous state to prevent duplicate broadcasts

        # Set up state change callbacks for each elevator
        for elevator in self.elevators:
            elevator.on_state_change = self._on_elevator_state_change

    
    def set_websocket_manager(self, ws_manager):  #Set the WebSocket manager for broadcasting updates
        self.ws_manager = ws_manager

    # ─────────────────────────────────────────────────────────────
    # ELEVATOR LIFECYCLE
    # ─────────────────────────────────────────────────────────────

    async def start(self): # Run all elevators concurrently
        self.running_tasks = [asyncio.create_task(elevator.run()) for elevator in self.elevators]
        
        # Wait for all elevator tasks (they run forever)
        await asyncio.gather(*self.running_tasks, return_exceptions=True)

    async def stop(self): # Stop all elevators and clean up
        for task in self.running_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for elevator in self.elevators:
            elevator.cleanup()
            del elevator
        
        self.total_floors = None    
        self.total_elevators = None
        self.elevators = None
        self.running_tasks = None
        self.ws_manager = None
        self.prev_state = None
    # ─────────────────────────────────────────────────────────────
    # ELEVATOR DISPATCH LOGIC (Collective Control)
    # ─────────────────────────────────────────────────────────────

    def add_request(self, floor: int, direction: str):
        best_elevator = self._select_elevator(floor, direction)
        self.elevators[best_elevator.id].add_request(floor, direction)
        return best_elevator.id

    def add_stop(self, elevator_id: int, floor: int):
        if elevator_id < 0 or elevator_id >= len(self.elevators):
            raise ValueError(f"Invalid elevator ID: {elevator_id}")
        
        self.elevators[elevator_id].add_stop(floor)

    def _select_elevator(self, floor: int, direction: str) -> Elevator:
        """
        Modified LOOK with Opportunistic Scheduling:
        1. Prefer elevator moving in same direction that will pass the floor (main sweep)
        2. Prefer elevator moving opposite but about to turn around near the floor (opportunistic)
        3. Else choose closest idle elevator
        4. Else fallback to least-loaded elevator (considering all 6 queues)
        """
        candidates = []

        # Rule 1: Same direction & will pass the floor (Main Sweep - Phase 1)
        for elevator in self.elevators:
            eff_dir = elevator.get_effective_direction()
            
            if eff_dir == direction:
                if direction == Direction.UP and elevator.current_floor <= floor:
                    candidates.append(elevator)
                elif direction == Direction.DOWN and elevator.current_floor >= floor:
                    candidates.append(elevator)

        if candidates:
            return min(candidates, key=lambda e: abs(e.current_floor - floor))

        # Rule 2: Opportunistic - Elevator going opposite direction but will turn around
        # Check if an elevator is about to reverse and can pick up this request
        for elevator in self.elevators:
            eff_dir = elevator.get_effective_direction()
            
            # Elevator going UP, request wants DOWN - check if elevator will turn around above floor
            if eff_dir == Direction.UP and direction == Direction.DOWN:
                # Get the highest floor this elevator will visit before turning
                turnaround_floor = self._get_turnaround_floor(elevator, Direction.UP)
                if turnaround_floor is not None and turnaround_floor >= floor:
                    candidates.append(elevator)
            
            # Elevator going DOWN, request wants UP - check if elevator will turn around below floor
            elif eff_dir == Direction.DOWN and direction == Direction.UP:
                # Get the lowest floor this elevator will visit before turning
                turnaround_floor = self._get_turnaround_floor(elevator, Direction.DOWN)
                if turnaround_floor is not None and turnaround_floor <= floor:
                    candidates.append(elevator)

        if candidates:
            # Prefer the one whose turnaround is closest to the requested floor
            return min(candidates, key=lambda e: self._estimated_arrival_time(e, floor, direction))

        # Rule 3: Idle elevators (prefer closest)
        idle_elevators = [
            e for e in self.elevators 
            if e.get_effective_direction() == Direction.IDLE
        ]
        if idle_elevators:
            return min(idle_elevators, key=lambda e: abs(e.current_floor - floor))

        # Rule 4: Least loaded elevator (fallback) - considering all 6 queues
        return min(
            self.elevators,
            key=lambda e: self._get_total_load(e)
        )

    def _get_total_load(self, elevator: Elevator) -> int:
        """Calculate total load across all 6 queues of the Modified LOOK scheduler"""
        return (
            len(elevator.internal_up.heap) +
            len(elevator.internal_down.heap) +
            len(elevator.up_up.heap) +
            len(elevator.down_down.heap) +
            len(elevator.up_down.heap) +
            len(elevator.down_up.heap)
        )

    def _get_turnaround_floor(self, elevator: Elevator, current_direction: str) -> int | None:
        """
        Get the floor where the elevator will turn around.
        For UP: returns the highest floor in up_up, internal_up, or up_down
        For DOWN: returns the lowest floor in down_down, internal_down, or down_up
        """
        if current_direction == Direction.UP:
            candidates = []
            if elevator.up_up.get_min() is not None:
                # For MinHeap, we need the max - but up_up stores floors to visit going up
                # The turnaround is the highest floor, so we check all values
                candidates.extend(elevator.up_up.heap)
            if elevator.internal_up.get_min() is not None:
                candidates.extend(elevator.internal_up.heap)
            if elevator.up_down.get_max() is not None:
                candidates.extend(elevator.up_down.heap)
            
            return max(candidates) if candidates else None
        
        elif current_direction == Direction.DOWN:
            candidates = []
            if elevator.down_down.get_max() is not None:
                candidates.extend(elevator.down_down.heap)
            if elevator.internal_down.get_max() is not None:
                candidates.extend(elevator.internal_down.heap)
            if elevator.down_up.get_min() is not None:
                candidates.extend(elevator.down_up.heap)
            
            return min(candidates) if candidates else None
        
        return None

    def _estimated_arrival_time(self, elevator: Elevator, floor: int, direction: str) -> int:
        """
        Estimate arrival time (in floors traveled) for opportunistic scheduling.
        This is a heuristic - actual time depends on stops and door operations.
        """
        eff_dir = elevator.get_effective_direction()
        current = elevator.current_floor
        
        if eff_dir == Direction.IDLE:
            return abs(current - floor)
        
        # Calculate distance including turnaround
        turnaround = self._get_turnaround_floor(elevator, eff_dir)
        
        if turnaround is None:
            return abs(current - floor)
        
        if eff_dir == Direction.UP and direction == Direction.DOWN:
            # Distance to turnaround + distance from turnaround to floor
            return (turnaround - current) + (turnaround - floor)
        
        elif eff_dir == Direction.DOWN and direction == Direction.UP:
            # Distance to turnaround + distance from turnaround to floor
            return (current - turnaround) + (floor - turnaround)
        
        return abs(current - floor)

#!----------------------------------------------------------------------------------------------------------------
    # ─────────────────────────────────────────────────────────────
    # REST-API STATUS
    # ─────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        return {
            "total_floors": self.total_floors,
            "total_elevators": self.total_elevators,
            "elevators": [
                elevator.get_status() for elevator in self.elevators
            ]
        }

    # ─────────────────────────────────────────────────────────────
    # STATUS & WEBSOCKET
    # ───────────────────────────────────────────────────────────── 
    #! THIS UNUSED ELEVATOR PARAM IS INTENTIONAL FOR CALLBACK SIGNATURE
    async def _on_elevator_state_change(self, elevator):
        await self._broadcast_state()

    async def _broadcast_state(self):
        if self.ws_manager is None:
            return

        try:
            loop = asyncio.get_running_loop()
            
            # Build current state (without timestamp for comparison)
            elevators_state = [
                elevator.get_status() for elevator in self.elevators
            ]
            
            # Check if state has changed (compare without timestamp)
            current_state_key = str(elevators_state)
            if self.prev_state == current_state_key:
                return  # No change, skip broadcast
            
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
