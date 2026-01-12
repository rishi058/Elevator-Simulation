from helper.models import RequestModel, ResponseMessage
from fastapi import HTTPException
from helper import global_elevator

async def add_request(req: RequestModel):
    elevator = global_elevator.elevator

    if elevator is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    floor = req.floor
    direction = req.direction.upper() 

    if direction not in ('U', 'D'):
        raise HTTPException(status_code=400, detail="Direction must be 'U' (up) or 'D' (down)")
    
    if floor < 0 or floor > elevator.total_floors:
        raise HTTPException(status_code=400, detail=f"Floor must be between 0 and {elevator.total_floors}")
    
    # Add the request and trigger re-evaluation
    elevator.add_request(floor, direction)
    
    return ResponseMessage(
        message=f"Request '{floor}{direction}' added successfully",
        success=True
    )