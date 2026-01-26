import asyncio
import sys
import os
import time

# Add root directory to path
sys.path.append(os.getcwd())

from backend.elevator.multi_elevator_system import CollectiveDispatchController
from backend.elevator.direction import Direction
from backend.elevator.elevator_system import Elevator

class TestScenarioRunner:
    def __init__(self):
        self.controller = None
    
    async def setup(self):
        self.controller = CollectiveDispatchController(total_floors=8, total_elevators=3)
        self.start_task = asyncio.create_task(self.controller.start())
        await asyncio.sleep(1) # Let it initialize

    async def teardown(self):
        await self.controller.stop()
        if self.start_task:
            self.start_task.cancel()
            try:
                await self.start_task
            except asyncio.CancelledError:
                pass
        print("\n--- Test Finished ---")

    async def wait_for_idle(self, timeout=30):
        start_time = time.time()
        while True:
            status = self.controller.get_status()
            elevators = status['elevators']
            if all(e['direction'] == Direction.IDLE for e in elevators):
                return True
            if time.time() - start_time > timeout:
                return False
            await asyncio.sleep(0.5)

    async def run_scenario_1_single_elevator_internal(self):
        print("\n[Scenario 1] Single Elevator Internal (0 -> 5)")
        # Test basic movement
        # Force Elevator 0 to be at 0 (it initialized there)
        
        e0 = self.controller.elevators[0]
        print(f"Initial State: E0 at {e0.current_floor}")
        
        # Internal Request to 5
        e0.add_stop(5)
        print("Added Internal Stop 5 to E0")
        
        # Wait for arrival
        while e0.current_floor != 5:
            await asyncio.sleep(0.5)
            if e0.current_floor > 5:
                print("FAILURE: Overshot target")
                return False
        
        print(f"Arrival check: E0 at {e0.current_floor}")
        return e0.current_floor == 5

    async def run_scenario_multi_dispatch_proximity(self):
        print("\n[Scenario 9] Multi-Elevator Dispatch - Proximity")
        # Elev 0 at 0 (IDLE)
        # Elev 1 at 7 (IDLE) - manually move it or mocking? we can set current_floor
        # Elev 2 at 3 (Moving UP to 5) - simulated
        
        e0 = self.controller.elevators[0]
        e1 = self.controller.elevators[1]
        e2 = self.controller.elevators[2]
        
        # Setup State
        e0.current_floor = 0.0
        e0.direction = Direction.IDLE
        
        e1.current_floor = 7.0
        e1.direction = Direction.IDLE
        
        e2.current_floor = 3.0
        e2.direction = Direction.UP
        e2.add_stop(5) # Set it in motion logic
        
        # Add Request 1U
        # Expect E0
        assigned_id = self.controller.add_request(1, Direction.UP)
        print(f"Request 1U assigned to: E{assigned_id}")
        
        if assigned_id == 0:
            print("SUCCESS: Assigned to closest IDLE elevator (E0)")
            return True
        else:
            print(f"FAILURE: Assigned to E{assigned_id} instead of E0")
            print(f"Costs: ")
            # Debug costs
            self.controller._get_best_elevator(1, Direction.UP)
            return False

    async def run_scenario_multi_dispatch_en_route(self):
        print("\n[Scenario 11] Multi-Elevator Dispatch - En-Route Optimization")
        # Elev 2 at 3 going to 5. Request 4U. Should be E2.
        
        e0 = self.controller.elevators[0]
        e0.current_floor = 0.0 # Far away
        
        e2 = self.controller.elevators[2]
        e2.current_floor = 3.0
        e2.direction = Direction.UP
        e2.add_stop(5)
        
        assigned_id = self.controller.add_request(4, Direction.UP)
        print(f"Request 4U assigned to: E{assigned_id}")
        
        if assigned_id == 2:
            print("SUCCESS: Assigned to En-Route elevator (E2)")
            return True
        else:
            print(f"FAILURE: Assigned to E{assigned_id} instead of E2")
            return False

    async def run_edge_case_dual_extremity(self):
        print("\n[Scenario 14] Edge Case - Dual Request at Extremity (7U, 7D)")
        # Request 7U and 7D against an elevator going to 7
        
        e0 = self.controller.elevators[0]
        e0.current_floor = 0.0
        
        # Add 7U and 7D. Should likely effectively be one stop logic or handled gracefully
        aid1 = self.controller.add_request(7, Direction.UP)
        aid2 = self.controller.add_request(7, Direction.DOWN)
        
        print(f"7U assigned E{aid1}, 7D assigned E{aid2}")
        
        # Wait until someone reaches 7
        timeout = 20
        start = time.time()
        while True:
            if any(e.current_floor == 7.0 for e in self.controller.elevators):
                print("Elevator reached floor 7")
                break
            if time.time() - start > timeout:
                print("Timeout reaching floor 7")
                return False
            await asyncio.sleep(1)
            
        await asyncio.sleep(2) # Allow door ops
        
        # Check if requests are cleared
        status = self.controller.get_status()
        active_reqs = False
        for e in status['elevators']:
            if 7 in e['external_up_requests'] or 7 in e['external_down_requests']:
                print(f"FAILURE: Request at 7 still active in E{e['elevator_id']}")
                active_reqs = True
        
        if not active_reqs:
            print("SUCCESS: Requests at 7 cleared")
            return True
        return False

async def main():
    runner = TestScenarioRunner()
    await runner.setup()
    
    try:
        results = []
        results.append(await runner.run_scenario_1_single_elevator_internal())
        await runner.wait_for_idle()
        
        results.append(await runner.run_scenario_multi_dispatch_proximity())
        await runner.wait_for_idle()
        
        results.append(await runner.run_scenario_multi_dispatch_en_route())
        await runner.wait_for_idle()
        
        results.append(await runner.run_edge_case_dual_extremity())
        await runner.wait_for_idle()
        
        print("\n" + "="*30)
        print(f"Passed: {results.count(True)} / {len(results)}")
        print("="*30)
        
    finally:
        await runner.teardown()

if __name__ == "__main__":
    asyncio.run(main())
