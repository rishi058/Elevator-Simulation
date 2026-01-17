from .direction import Direction
from .ui_state_manager import UIStateManager
import asyncio, copy

class Elevator(UIStateManager):    
    def __init__(self, elevator_id: int, total_floors=10):
        super().__init__(elevator_id, total_floors)
        self.on_state_change = None  # Callback for state change notifications
        
    async def run(self):
        while True:
            self.update_ui_requests()

            stop = self.get_next_stop()
            if stop is None:
                self.direction = Direction.IDLE
                await self._notify_state_change()
                await asyncio.sleep(1)
                continue  
            
            # FIX 1: Handle "Already Here" Case [ We are already at the target. Just open door.]
            # Do NOT change direction (keep previous moving direction logic if needed) Only set direction if we actually need to move
            if stop != self.current_floor:
                self.direction = Direction.UP if stop > self.current_floor else Direction.DOWN
            
            await self._notify_state_change()

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
                await self._notify_state_change()
                await asyncio.sleep(1)

            # Arrival Logic
            self.is_door_open = True
            self.moving_direction = self.direction  # used for UI & eff dir     
            # --- FIX 2: Maintain Direction State on Arrival ---
            # Don't immediately set IDLE. Let the scheduler decide next loop.
            
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
        self.total_floors = 0
        self.current_floor = 0  
        self.direction = Direction.IDLE
        self.is_door_open = False
        self.moving_direction = Direction.IDLE
        self.internal_up = None
        self.internal_down = None
        self.up_up = None
        self.down_down = None
        self.up_down = None
        self.down_up = None