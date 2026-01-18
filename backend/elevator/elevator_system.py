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
                # --- FIX: Clean State Reset on IDLE ---
                self.direction = Direction.IDLE
                self.moving_direction = Direction.IDLE
                # Ensure door is closed logic if needed, usually managed by is_door_open
                
                await self.broadcast_state()
                await asyncio.sleep(1)
                continue  
            
            # Decide initial direction
            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self.broadcast_state()

            # Wait for door to close before moving
            while self.is_door_open:
                await asyncio.sleep(1)
            
            # --- MOVE LOOP ---
            while self.current_floor != stop: 
                # Check for interruptions (Phase 1 logic)
                new_stop = self.get_next_stop(delete=False, only_same_direction=True)
                
                interrupt = False
                if new_stop is not None:
                    # Logic: If we are going UP, and new_stop is closer (and above us), take it.
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        interrupt = True
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        interrupt = True
                
                if interrupt:
                    # 1. Consume the new closer stop
                    self.get_next_stop(delete=True, only_same_direction=True)
                    
                    # 2. Re-queue the OLD 'stop' correctly
                    requeued = False
                    
                    # Check UI state to restore requests to correct heaps
                    if stop in self.ui_internal_requests:
                        self.add_stop(stop)
                        requeued = True
                    
                    # FIX: Handle sets carefully. 
                    # If it was an external DOWN request, put it back as DOWN (Phase 2 Turnaround)
                    if stop in self.ui_external_down_requests:
                        self.add_request(stop, Direction.DOWN)
                        requeued = True
                        
                    if stop in self.ui_external_up_requests:
                        self.add_request(stop, Direction.UP)
                        requeued = True
                    
                    # Fallback
                    if not requeued:
                        self.add_stop(stop)

                    # 3. Update target
                    stop = new_stop
                    
                    # 4. Broadcast immediately to reflect target change
                    await self.broadcast_state()

                # Simulation Step
                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self.broadcast_state()
                await asyncio.sleep(1)

            # --- ARRIVAL LOGIC ---
            self.is_door_open = True
            
            # Capture the direction we arrived in for UI indicators
            self.moving_direction = self.direction            
            
            self.update_ui_requests() 
            await self.broadcast_state()
            
            # Open door time
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