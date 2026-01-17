from fastapi import FastAPI
from helper.router import custom_router
import uvicorn

from helper import global_elevator
from contextlib import asynccontextmanager
import asyncio
from fastapi.middleware.cors import CORSMiddleware

from helper.websocket_manager import ws_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic 

    yield

    # Shutdown Logic
    task = global_elevator.elevator_task
    if task:
        print("[System] Stopping elevator service...")
        global_elevator.elevator.cleanup()
        del global_elevator.elevator

        task.cancel()
        try:
            await task
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
        "message": "Welcome to Elevator Microservice",
        "endpoints": {
            "GET /status": "Get current elevator status",
            "POST /request": "Add a floor request with direction (e.g., '5U', '3D')",
            "POST /stop": "Add a stop at a specific floor",
            "POST /total_floors": "Set the total number of floors in the building",

            "WS /api/ws": "WebSocket connection for real-time elevator status updates",   
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # reload=True sometime creates issues while shutting down
