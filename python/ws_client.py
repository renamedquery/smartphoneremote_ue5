# import asyncio
# import websockets
#
# async def hello():
#     async with websockets.connect(
#             'ws://localhost:6302/ws') as websocket:
#
#         # wait websocket.send("test")
#
#         greeting = await websocket.recv()
#         print(greeting)
#
# asyncio.get_event_loop().run_until_complete(hello())

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
print(s.getsockname()[0])
s.close()
