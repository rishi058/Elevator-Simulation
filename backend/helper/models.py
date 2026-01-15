from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────

class RequestModel(BaseModel):
    floor: int
    direction: str
    
    class Config:
        json_schema_extra = {
            "example": {"floor": 5, "direction": "U"}
        }

class StopModel(BaseModel):
    elevator_id: int
    floor: int
    
    class Config:
        json_schema_extra = {
            "example": {"elevator_id": 1, "floor": 7}
        }

class ElevatorStatus(BaseModel):
    elevator_id: int
    current_floor: float
    direction: str
    is_door_open: bool
    up_stops: list[int] = []
    down_stops: list[int] = []

class MultiElevatorStatus(BaseModel):
    total_floors: int
    elevators: list[ElevatorStatus]

class BuildingModel(BaseModel):
    total_floors: int
    total_elevators: int

class ResponseMessage(BaseModel):
    message: str
    success: bool