import asyncio
import sys
import os

# Add the current directory to sys.path to ensure imports work
sys.path.append(os.getcwd())

from backend.elevator.multi_elevator_system import CollectiveDispatchController
from backend.elevator.direction import Direction

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("log.txt", "w", encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Ensure flush

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()

def print_tree(tree):
    nodes = []
    def traverse(node):
        if not node: return
        traverse(node.left)
        nodes.append(node.key)
        traverse(node.right)
    traverse(tree.root)
    return nodes

async def main():
    print("Starting simulation...")
    # Initialize controller with 7 floors (0-6) and 3 elevators
    controller = CollectiveDispatchController(total_floors=7, total_elevators=3)
    
    # Start controller in a background task as it awaits internal tasks
    start_task = asyncio.create_task(controller.start())

    # Give it a moment to initialize
    await asyncio.sleep(1)

    requests = [
        (6, Direction.DOWN),
        (5, Direction.UP),
        (5, Direction.DOWN),
        (4, Direction.UP),
        (4, Direction.DOWN),
        (3, Direction.UP),
        (3, Direction.DOWN)
    ]

    print("Adding requests...")
    for floor, direction in requests:
        aid = controller.add_request(floor, direction)
        print(f"Requesting: {floor} {direction} -> Assigned to E{aid}")

    print("Requests added. Waiting for elevators to handle them...")

    # Wait for completion (simulation)
    # We expect all elevators to return to IDLE eventually.
    timeout = 120 # seconds (increased timeout as elevators might take time)
    start_time = asyncio.get_event_loop().time()
    
    while True:
        status = controller.get_status()
        elevators = status['elevators']
        
        all_idle = True
        for elev in elevators:
            if elev['direction'] != Direction.IDLE:
                all_idle = False
                break
        
        current_time = asyncio.get_event_loop().time()
        
        if all_idle and (current_time - start_time > 10): 
             # Wait a bit more to ensure it's stable
             break
        
        if current_time - start_time > timeout:
            print("Timeout waiting for idle")
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
            print(f"  -> HAS LINGERING REQUESTS")
            found_bug = True
            
    if found_bug:
        print("\nBUG REPRODUCED: Some buttons stayed ON.")
    else:
        print("\nNo bug found. All requests cleared.")

    controller.stop()

if __name__ == "__main__":
    asyncio.run(main())
