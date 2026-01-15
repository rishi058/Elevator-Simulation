from helper.models import BuildingModel, ResponseMessage
from helper import global_elevator
from elevator.elevator import Elevator
from helper.websocket_manager import ws_manager
import asyncio

async def set_floors(building: BuildingModel):
    if global_elevator.elevator_task:
        print("[System] Shutting down Old Elevator System...")

        global_elevator.elevator.cleanup()
        del global_elevator.elevator
        
        global_elevator.elevator_task.cancel()
        try:
           await global_elevator.elevator_task
        except asyncio.CancelledError:
           pass
    
    print(f"[System] New Elevator Sytem Starting....")
    global_elevator.elevator = Elevator(building.total_floors)  # Only this way you can initialize gloval variable

    global_elevator.elevator.set_websocket_manager(ws_manager)  # Set WebSocket manager

    global_elevator.elevator_task = asyncio.create_task(global_elevator.elevator.run())

    print(f"[System] Elevator initialized with {building.total_floors} floors...")
   
    return ResponseMessage(
        message=f"Total floors set to {building.total_floors} successfully",
        success=True
    )
