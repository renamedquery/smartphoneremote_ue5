import asyncio
import websockets

async def hello():
    async with websockets.connect(
            'ws://localhost:6302/ws') as websocket:

        # wait websocket.send("test")

        greeting = await websocket.recv()
        print(greeting)

asyncio.get_event_loop().run_until_complete(hello())
