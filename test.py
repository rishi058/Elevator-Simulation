import asyncio
import aiohttp
import random

async def chaos_test():
    """Maximum chaos - all race conditions at once"""
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for _ in range(20):  # 20 concurrent requests
                floor = random.randint(0, 9)
                direction = random.choice(["U", "D"])
                
                # Randomly choose endpoint
                if random.random() < 0.5:
                    task = session.post("http://localhost:8000/api/request", 
                                       json={"floor": floor, "direction": direction})
                else:
                    task = session.post("http://localhost:8000/api/stop", 
                                       json={"floor": floor})
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(0.5)  # Brief pause, then repeat

asyncio.run(chaos_test())