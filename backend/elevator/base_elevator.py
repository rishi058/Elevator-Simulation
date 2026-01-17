from .direction import Direction
import asyncio

class BaseElevator:
    """Core elevator state and door operations"""
    
    def __init__(self, elevator_id: int, total_floors=10):
        self.id = elevator_id
        self.total_floors = total_floors  #! Useless 
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.is_door_open = False
        self.moving_direction = Direction.IDLE
    
    async def open_door(self):
        """Open door for 5 seconds"""
        self.is_door_open = True
        await asyncio.sleep(5)
        self.is_door_open = False
    
    def get_effective_direction(self):
        """Get the current effective direction of the elevator"""
        if self.direction != Direction.IDLE:
            return self.direction
        if self.is_door_open:
            return self.moving_direction
        return Direction.IDLE