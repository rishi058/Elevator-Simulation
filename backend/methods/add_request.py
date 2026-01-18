from helper.models import RequestModel, ResponseMessage
from fastapi import HTTPException
from helper import global_controller

async def add_request(req: RequestModel):
    """Handle hall call request - someone waiting at a floor"""
    controller = global_controller.controller

    if controller is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    floor = req.floor
    direction = req.direction.upper()

    if direction not in ('U', 'D'):
        raise HTTPException(status_code=400, detail="Direction must be 'U' (up) or 'D' (down)")
    
    if floor < 0 or floor > controller.total_floors:
        raise HTTPException(status_code=400, detail=f"Floor must be between 0 and {controller.total_floors}")
    
    # Dispatch to best elevator using Collective Control
    controller.add_request(floor, direction)
    
    return ResponseMessage(
        message=f"Request '{floor}{direction}' is successfully added to the system.",
        success=True
    )