from elevator.elevator_system import Elevator 
import asyncio

elevator: Elevator = None 
elevator_task: asyncio.Task = None