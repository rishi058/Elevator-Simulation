from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from methods.add_request import add_request 
from methods.add_stop import add_stop
from methods.get_status import get_status
from methods.initialize_building import initialize_building

from .models import RequestModel, StopModel, BuildingModel
from .websocket_manager import ws_manager

custom_router = APIRouter(prefix='/api', tags=["Elevator"]) 

@custom_router.get("/status")
async def get_status_route():
    return await get_status()

@custom_router.post("/request")
async def add_request_route(request: RequestModel):
    return await add_request(request)

@custom_router.post("/stop")
async def add_stop_route(stop: StopModel):
    return await add_stop(stop)

@custom_router.post("/building")
async def initialize_building_route(building: BuildingModel):
    return await initialize_building(building)

@custom_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages if needed
            data = await websocket.receive_text()
            # You can handle client commands here if needed
            # For now, just echo back or ignore
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        ws_manager.disconnect(websocket)