from elevator.multi_elevator_system import CollectiveDispatchController 
import asyncio

controller: CollectiveDispatchController = None
controller_task: asyncio.Task = None