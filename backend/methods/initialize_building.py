from helper.models import BuildingModel, ResponseMessage
from fastapi import HTTPException
from helper import global_controller
from elevator.multi_elevator_system import CollectiveDispatchController
import asyncio
from helper.websocket_manager import ws_manager


async def initialize_building(building: BuildingModel):
    controller_task = global_controller.controller_task

    if controller_task:
        print("[System] Shutting down Old Elevator System") 

        await global_controller.controller.stop()
        del global_controller.controller
        
        controller_task.cancel()
        try:
            await controller_task
        except asyncio.CancelledError:
            pass

    print(f"[System] Initializing Building with {building.total_floors} floors and {building.total_elevators} elevators")

    global_controller.controller = CollectiveDispatchController(building.total_floors, building.total_elevators)

    global_controller.controller.set_websocket_manager(ws_manager)

    global_controller.controller_task = asyncio.create_task(global_controller.controller.start())
   
    return ResponseMessage(
        message=f"Building initialized with {building.total_floors} floors and {building.total_elevators} elevators successfully",
        success=True
    )
