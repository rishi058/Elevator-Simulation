from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio, copy

class Elevator(UIStateManager):    
    def __init__(self, total_floors=10):
        super().__init__(total_floors)
        self.ws_manager = None
        self.prev_state = None
    
    def set_websocket_manager(self, ws_manager):
        self.ws_manager = ws_manager
    
    async def broadcast_state(self):
        if self.ws_manager is None:
            return

        moving_direction = self.get_effective_direction()

        try:
            loop = asyncio.get_running_loop()

            state = {
                "current_floor": self.current_floor,
                "direction": moving_direction,
                "is_door_open": self.is_door_open,
                "external_up_requests": list(self.ui_external_up_requests),
                "external_down_requests": list(self.ui_external_down_requests),
                "internal_requests": list(self.ui_internal_requests),
            }

            current_state_key = str(state)
            if self.prev_state == current_state_key:
                return
            
            self.prev_state = current_state_key
            state["timestamp"] = loop.time()
            await self.ws_manager.broadcast(state)
        except Exception as e:
            print(f"[Controller] Error broadcasting state: {e}")

    
    async def run(self):
        while True:
            self.update_ui_requests()  # Helps When lift is IDLE and request comes for current floor 

            stop = self.get_next_stop()
            if stop is None:
                self.direction = Direction.IDLE
                await self.broadcast_state()
                await asyncio.sleep(1)
                continue  
            
            self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            await self.broadcast_state()   # Notify direction change

            while self.is_door_open:    # Wait until door is closed[Edge case]
                await asyncio.sleep(1)
            
            while self.current_floor != stop: 
                # Check if there's a closer stop in the same direction
                new_stop = self.get_next_stop(delete=False)
                if new_stop is not None:
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        self.get_next_stop()
                        self.up_stops.insert(stop)
                        stop = new_stop
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        self.get_next_stop()
                        self.down_stops.insert(stop)
                        stop = new_stop

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                print(f"[Elevator Moving] Current Floor: {self.current_floor}")
                await self.broadcast_state()
                await asyncio.sleep(1)

            # Arrival Logic
            print(f"[Elevator] Arrived at floor: {self.current_floor}")
            self.is_door_open = True
            self.moving_direction = self.direction            
            self.direction = Direction.IDLE
            
            self.update_ui_requests() 
            await self.broadcast_state()
            await asyncio.sleep(5)  # We cant use [asyncio.create_task(self.open_door())] here bcz we need to wait until door is closed
            self.is_door_open = False
            await self.broadcast_state()

    def cleanup(self):
        """Clean up elevator resources"""
        self.total_floors = 0
        self.current_floor = 0  
        self.direction = Direction.IDLE
        self.is_door_open = False
        self.moving_direction = Direction.IDLE
        self.up_stops = None
        self.down_stops = None
        self.ws_manager = None
        self.prev_state = None