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
