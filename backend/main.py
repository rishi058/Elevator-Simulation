from fastapi import FastAPI
from helper.router import custom_router
import uvicorn

from helper import global_controller
from elevator.multi_elevator_system import CollectiveDispatchController
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.cors import CORSMiddleware

from helper.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    
    yield
    
    # Shutdown
    controller_task = global_controller.controller_task
    if controller_task:
        print("[System] Shutting down Elevator System") 

        await global_controller.controller.stop()  # stop each elevator gracefully
        del global_controller.controller

        controller_task.cancel()
        try:
            await controller_task
        except asyncio.CancelledError:
            pass
        
    print("[System] Elevator service stopped")

app = FastAPI(title="Elevator Microservice", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allowed origins
    allow_credentials=True,
    allow_methods=["*"],        # Allowed HTTP methods
    allow_headers=["*"],        # Allowed headers
)
app.include_router(custom_router)

@app.get("/", tags=["Info"])
async def root():
    return {
        "message": "Welcome to Multi-Elevator Microservice",
        "endpoints": {
            "GET /api/status": "Get status of all elevators",
            "POST /api/request": "Hall call - request elevator at floor with direction (e.g., floor=5, direction='U')",
            "POST /api/stop": "Car call - add stop for specific elevator (e.g., elevator_id=0, floor=7)",
            "POST /api/total_floors": "Set the total number of floors in the building",
            "WS /api/ws": "WebSocket connection for real-time elevator status updates",   
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
