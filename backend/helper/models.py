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
    
    external_up_requests: list[int]
    external_down_requests: list[int]
    internal_requests: list[int]

class BuildingModel(BaseModel):
    total_floors: int

class ResponseMessage(BaseModel):
    message: str
    success: bool