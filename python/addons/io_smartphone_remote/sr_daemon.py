import asyncio
import websockets
import subprocess
import os

import logging
from . import async_loop as  al
import httpd
import bpy
import sys
import socket
from bpy.app.handlers import persistent


class CameraProcessProtocol(asyncio.SubprocessProtocol):
    def __init__(self, exit_future):
        self.exit_future = exit_future
        self.output = bytearray()

    def pipe_data_received(self, fd, data):
        self.output.extend(data)

    def process_exited(self):
        self.exit_future.set_result(True)

@asyncio.coroutine
def get_frame(loop):
    exit_future = asyncio.Future(loop=loop)

    # Create the subprocess controlled by the protocol CameraProcessProtocol,
    # redirect the standard output into a pipe
    create = loop.subprocess_exec(lambda: CameraProcessProtocol(exit_future),
                                  '/home/slumber/Repos/DeviceTracking/build/DeviceTracking',
                                  stdin=None, stderr=None)
    transport, protocol = yield from create

    # Wait for the subprocess exit using the process_exited() method
    # of the protocol
    yield from exit_future

    # Close the stdout pipe
    transport.close()

    # Read the output which was collected by the pipe_data_received()
    # method of the protocol
    data = bytes(protocol.output)
    return data.decode('ascii').rstrip()

async def WebsocketRecv(websocket, path):
    import bpy
    print("starting websocket server on 5678")
    offset = [0.0, 0.0, 0.0]
    while True:
        data = await websocket.recv()
        print(data)
        if 'sensors' in path:
            sensors = data.split('/')
            bpy.context.selected_objects[0].rotation_euler[2] = float(
                sensors[0]) + offset[2]
            bpy.context.selected_objects[0].rotation_euler[1] = float(
                sensors[1]) + offset[1]
            bpy.context.selected_objects[0].rotation_euler[0] = float(
                sensors[2]) + offset[0]
            #bpy.context.selected_objects[0].location[0] += float(sensors[0]/2)
            #bpy.context.selected_objects[0].location[1] += float(sensors[1]/2)
            #bpy.context.selected_objects[0].location[2] += float(sensors[2]/2)
        elif 'commands' in path:
            print("init rotation")
            sensors = data.split('/')
            offset = [
                (float(sensors[3]) -
                 bpy.context.selected_objects[0].rotation_euler[0]),
                (float(sensors[2]) -
                 bpy.context.selected_objects[0].rotation_euler[1]),
                (float(sensors[1]) - bpy.context.selected_objects[0].rotation_euler[2])]

async def CameraFeed():
    # Wait for ImageProcess
    await asyncio.sleep(2)
    async with websockets.connect(
            'ws://localhost:6302/ws') as cli:
        print("connecting")
        cli.send("start_slam")
        while True:
            t = await cli.recv()
            print(t)

def GetCurrentIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def done_callback(task):
    print('Task result: ', task.result())



@persistent
def launchDaemon(scene):
    logging.basicConfig(level=logging.DEBUG)

    _ip = GetCurrentIp()


    if sys.platform == "win32":
        _loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(_loop)
    else:
        _loop = asyncio.get_event_loop()

    try:
        al.setup_asyncio_executor()
        al.register()
        print("async_loop setuping")
    except:
        print("async_loop already setup")
        pass

    root = os.path.dirname(os.path.abspath(os.path.join(__file__,"../../..")))+"/static"
    print("launch server on " + _ip+ root)
    _httpd = _loop.create_server(lambda: httpd.HttpProtocol(_ip, root),
                                 '0.0.0.0',
                                 8080)

    _wsd = websockets.serve(WebsocketRecv, '0.0.0.0', 5678)

    websocket_task = asyncio.ensure_future(_wsd)
    # httpd_task = _loop.run_until_complete(_httpd)
    httpd_task = asyncio.ensure_future(_httpd)

    # camera_task = asyncio.ensure_future(get_frame(_loop))
    # camera_feed_task = asyncio.ensure_future(CameraFeed())
    #
    al.ensure_async_loop()

    #_loop.run_forever()
    # bpy.app.handlers.load_post.clear()

def register():
    bpy.app.handlers.load_post.append(launchDaemon)
    # Launch()


def unregister():
    bpy.app.handlers.load_post.clear()
    print('test', sep=' ', end='n', file=sys.stdout, flush=False)
