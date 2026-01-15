from .direction import Direction
from .elevator import Elevator
import asyncio

# Collective Control Dispatch System
# Uses SCAN algorithm for each elevator and smart dispatching

class CollectiveDispatchController:
    def __init__(self, total_floors: int = 10, total_elevators: int = 3):
        self.total_floors = total_floors
        self.elevator_count = total_elevators
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
        self.elevator_count = None
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
        Collective Control selection rules:
        1. Prefer elevator already moving in same direction and approaching the floor
        2. Else choose closest idle elevator
        3. Else fallback to least-loaded elevator
        """
        candidates = []

        # Rule 1: Same direction & will pass the floor
        for elevator in self.elevators:
            eff_dir = elevator.get_effective_direction()
            
            if eff_dir == direction:
                if direction == Direction.UP and elevator.current_floor <= floor:
                    candidates.append(elevator)
                elif direction == Direction.DOWN and elevator.current_floor >= floor:
                    candidates.append(elevator)

        if candidates:
            return min(candidates, key=lambda e: abs(e.current_floor - floor))

        # Rule 2: Idle elevators (prefer closest)
        idle_elevators = [
            e for e in self.elevators 
            if e.get_effective_direction() == Direction.IDLE
        ]
        if idle_elevators:
            return min(idle_elevators, key=lambda e: abs(e.current_floor - floor))

        # Rule 3: Least loaded elevator (fallback)
        return min(
            self.elevators,
            key=lambda e: len(e.up_stops.heap) + len(e.down_stops.heap)
        )

#!----------------------------------------------------------------------------------------------------------------

    # ─────────────────────────────────────────────────────────────
    # STATUS & WEBSOCKET
    # ─────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get status of all elevators"""
        return {
            "total_floors": self.total_floors,
            "elevator_count": self.elevator_count,
            "elevators": [
                elevator.get_status() for elevator in self.elevators
            ]
        }

    def get_elevator_status(self, elevator_id: int) -> dict:   # Get status of a specific elevator
        if elevator_id < 0 or elevator_id >= len(self.elevators):
            raise ValueError(f"Invalid elevator ID: {elevator_id}")
        return self.elevators[elevator_id].get_status()

    async def _on_elevator_state_change(self, elevator):
        """Callback when an elevator's state changes"""
        await self._broadcast_state()

    async def _broadcast_state(self):
        """Broadcast current state of all elevators to WebSocket clients"""
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
