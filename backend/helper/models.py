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
    floor: int
    
    class Config:
        json_schema_extra = {
            "example": {"floor": 7}
        }

class ElevatorStatus(BaseModel):
    current_floor: float
    direction: str
    is_door_open: bool
    # message: str
    # is_moving: bool

class BuildingModel(BaseModel):
    total_floors: int

class ResponseMessage(BaseModel):
    message: str
    success: bool