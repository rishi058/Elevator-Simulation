from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio

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
                # Clean reset when IDLE
                self.direction = Direction.IDLE
                self.moving_direction = Direction.IDLE
                await self.broadcast_state()
                await asyncio.sleep(1)
                continue  
            
            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self.broadcast_state()

            while self.is_door_open:
                await asyncio.sleep(1)
            
            # --- MOVE LOOP ---
            while self.current_floor != stop: 
                new_stop = self.get_next_stop(delete=False)
                
                # Robust Interrupt Check
                if new_stop is not None:
                    interrupt = False
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        interrupt = True
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        interrupt = True
                
                    if interrupt:
                        self.get_next_stop(delete=True)  # delete the new stop
                        requeued_any = False             # Robust Re-queueing
                        
                        # --- Add back old stop ---
                        if stop in self.ui_internal_requests:
                            self.add_stop(stop)  
                            requeued_any = True
                        
                        if stop in self.ui_external_down_requests:
                            self.add_request(stop, Direction.DOWN)
                            requeued_any = True
                            
                        if stop in self.ui_external_up_requests:
                            self.add_request(stop, Direction.UP)
                            requeued_any = True
                        
                        # Fallback: If not found in UI sets (rare), default to Internal
                        if not requeued_any: self.add_stop(stop)
                        
                        stop = new_stop  # Update to new stop
                        await self.broadcast_state()

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self.broadcast_state()
                await asyncio.sleep(1)

            # --- ARRIVAL ---
            self.is_door_open = True
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
        #----------------------------------------
        self.up_up = None
        self.down_down = None
        self.up_down = None
        self.down_up = None
        self.internal_up = None
        self.internal_down = None
        #----------------------------------------
        self.ui_external_up_requests = None
        self.ui_external_down_requests = None
        self.ui_internal_requests = None
        #----------------------------------------
        self.ws_manager = None
        self.prev_state = None