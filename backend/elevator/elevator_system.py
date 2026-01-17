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
            self.update_ui_requests()

            stop = self.get_next_stop()
            if stop is None:
                self.direction = Direction.IDLE
                await self.broadcast_state()
                await asyncio.sleep(1)
                continue  
            
            # --- FIX 1: Handle "Already Here" Case ---
            if stop == self.current_floor:
                # We are already at the target. Just open door.
                # Do NOT change direction (keep previous moving direction logic if needed)
                pass 
            else:
                # Only set direction if we actually need to move
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self.broadcast_state()

            # Wait for door to close before moving
            while self.is_door_open:
                await asyncio.sleep(1)
            
            # Move loop
            while self.current_floor != stop: 
                # Check for interruptions (Phase 1 logic)
                new_stop = self.get_next_stop(delete=False, only_same_direction=True)
                
                if new_stop is not None:
                    # Logic: If we are going UP, and new_stop is closer (and above us), take it.
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        self.get_next_stop(delete=True, only_same_direction=True) 
                        self.add_stop(stop) 
                        stop = new_stop
                    
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        self.get_next_stop(delete=True, only_same_direction=True) 
                        self.add_stop(stop)
                        stop = new_stop

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self.broadcast_state()
                await asyncio.sleep(1)

            # Arrival Logic
            self.is_door_open = True
            
            # --- FIX 2: Maintain Direction State on Arrival ---
            # Don't immediately set IDLE. Let the scheduler decide next loop.
            # self.moving_direction can be used for UI indicators (arrows)
            self.moving_direction = self.direction            
            
            self.update_ui_requests() 
            await self.broadcast_state()
            await asyncio.sleep(5) 
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