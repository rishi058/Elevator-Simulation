from helper.models import StopModel, ResponseMessage 
from fastapi import HTTPException
from helper import global_elevator

async def add_stop(stop: StopModel):
    elevator = global_elevator.elevator

    if elevator is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    if stop.floor < 0 or stop.floor > elevator.total_floors:
        raise HTTPException(status_code=400, detail=f"Floor must be between 0 and {elevator.total_floors}")
    
    elevator.add_stop(stop.floor)
    
    return ResponseMessage(
        message=f"Stop at floor {stop.floor} added successfully",
        success=True
    )
