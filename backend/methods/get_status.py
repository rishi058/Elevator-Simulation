from fastapi import HTTPException
from helper.models import ElevatorStatus
from elevator.direction import Direction

from helper import global_elevator

async def get_status(): 
    elevator = global_elevator.elevator 
       
    if elevator is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    moving_direction = elevator.direction
    if moving_direction==Direction.IDLE and elevator.is_door_open:
        moving_direction = elevator.moving_direction
    
    return ElevatorStatus(
        current_floor=elevator.current_floor,
        direction=moving_direction,
        is_door_open=elevator.is_door_open,
        external_up_requests=list(elevator.ui_external_up_requests),
        external_down_requests=list(elevator.ui_external_down_requests),
        internal_requests=list(elevator.ui_internal_requests)
    )