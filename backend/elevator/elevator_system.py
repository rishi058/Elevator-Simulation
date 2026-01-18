from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio, copy

class Elevator(UIStateManager):    
    def __init__(self, id: int, total_floors=10):
        super().__init__(id, total_floors)
        self.on_state_change = None  # Callback for state change notifications
        
    async def run(self):
        while True:
            self.update_ui_requests()

            stop = self.get_next_stop()
            if stop is None:
                # Clean reset when IDLE
                self.direction = Direction.IDLE
                self.moving_direction = Direction.IDLE
                await self._notify_state_change()
                await asyncio.sleep(1)
                continue  
            
            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self._notify_state_change()

            while self.is_door_open:
                await asyncio.sleep(1)
            
            # --- MOVE LOOP ---
            while self.current_floor != stop: 
                new_stop = self.get_next_stop(delete=False, only_same_direction=True)
                interrupt = False
                
                # Robust Interrupt Check
                if new_stop is not None:
                    if self.direction == Direction.UP and new_stop < stop and new_stop > self.current_floor:
                        interrupt = True
                    elif self.direction == Direction.DOWN and new_stop > stop and new_stop < self.current_floor:
                        interrupt = True
                
                if interrupt:
                    self.get_next_stop(delete=True, only_same_direction=True)
                    
                    # Robust Re-queueing
                    requeued_any = False
                    
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
                    if not requeued_any:
                        self.add_stop(stop)
                    
                    stop = new_stop
                    await self._notify_state_change()

                self.current_floor += 0.2 if self.direction == Direction.UP else -0.2
                self.current_floor = round(self.current_floor, 1)
                await self._notify_state_change()
                await asyncio.sleep(1)

            # --- ARRIVAL ---
            self.is_door_open = True
            self.moving_direction = self.direction            
            self.update_ui_requests() 
            await self._notify_state_change()
            await asyncio.sleep(5) 
            self.is_door_open = False
            await self._notify_state_change()


    #!---------------------------------------------------------------------------------
    
    async def _notify_state_change(self): # Notify Controller about state change
        if self.on_state_change:
            await self.on_state_change(self)
    
    def get_status(self) -> dict:
        return {
            "elevator_id": self.id,
            "current_floor": self.current_floor,
            "direction": self.get_effective_direction(),
            "is_door_open": self.is_door_open,
            "external_up_requests": list(self.ui_external_up_requests),
            "external_down_requests": list(self.ui_external_down_requests),
            "internal_requests": list(self.ui_internal_requests),
        }
    
    #!---------------------------------------------------------------------------------

    def cleanup(self):
        """Clean up elevator resources"""
        self.id = None
        self.total_floors = None
        self.current_floor = None  
        self.direction = None
        self.is_door_open = None
        self.moving_direction = None
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
        self.on_state_change = None
        