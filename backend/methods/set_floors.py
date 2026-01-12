from helper.models import BuildingModel, ResponseMessage
from helper import global_elevator

async def set_floors(building: BuildingModel):
    global_elevator.elevator.total_floors = building.total_floors
   
    return ResponseMessage(
        message=f"Total floors set to {building.total_floors} successfully",
        success=True
    )
