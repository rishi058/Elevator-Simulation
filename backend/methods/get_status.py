from fastapi import HTTPException
from helper.models import MultiElevatorStatus, ElevatorStatus
from elevator.direction import Direction

from helper import global_controller

async def get_status():
    controller = global_controller.controller
       
    if controller is None:
        raise HTTPException(status_code=503, detail="Elevator service not initialized")
    
    status = controller.get_status()
    
    elevator_statuses = [
        ElevatorStatus(
            elevator_id=e["elevator_id"],
            current_floor=e["current_floor"],
            direction=e["direction"],
            is_door_open=e["is_door_open"],
            external_up_requests=e["external_up_requests"],
            external_down_requests=e["external_down_requests"],
            internal_requests=e["internal_requests"]
        )
        for e in status["elevators"]
    ]
    
    return MultiElevatorStatus(
        total_floors=status["total_floors"],
        total_elevators=status["total_elevators"],  
        elevators=elevator_statuses
    )