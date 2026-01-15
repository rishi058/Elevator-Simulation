from helper.models import StopModel, ResponseMessage 
from fastapi import HTTPException
from helper import global_controller

async def add_stop(stop: StopModel):
    """Handle car call - someone inside elevator pressed a floor button"""
    controller = global_controller.controller

    if controller is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    elevator_id = stop.elevator_id
    floor = stop.floor

    if elevator_id < 0 or elevator_id >= controller.total_elevators:
        raise HTTPException(
            status_code=400, 
            detail=f"Elevator ID must be between 0 and {controller.total_elevators - 1}"
        )
    
    if floor < 0 or floor > controller.total_floors:
        raise HTTPException(
            status_code=400, 
            detail=f"Floor must be between 0 and {controller.total_floors}"
        )
    
    controller.add_stop(elevator_id, floor)
    
    return ResponseMessage(
        message=f"Stop at floor {floor} added to Elevator {elevator_id}",
        success=True
    )
