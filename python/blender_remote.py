import asyncio
import websockets
import subprocess
import os
import httpd
import logging
from BlenderRemote import async_loop
import bpy

async def WebsocketRecv(websocket, path):
    import bpy
    print("starting websocket server on 5678")
    offset = [0.0,0.0,0.0]
    while True:
        data = await websocket.recv()
        if 'sensors' in path:
            sensors = data.split('/')
            bpy.context.selected_objects[0].rotation_euler[2] = float(sensors[0]) + offset[2];
            bpy.context.selected_objects[0].rotation_euler[1] = float(sensors[1]) +offset[1];
            bpy.context.selected_objects[0].rotation_euler[0] =  float(sensors[2])+ offset[0];
            #bpy.context.selected_objects[0].location[0] += float(sensors[0]/2)
            #bpy.context.selected_objects[0].location[1] += float(sensors[1]/2)
            #bpy.context.selected_objects[0].location[2] += float(sensors[2]/2)
        elif 'commands' in path:
            print("init rotation")
            sensors = data.split('/')
            offset = [
                (float(sensors[3]) -bpy.context.selected_objects[0].rotation_euler[0]),
                (float(sensors[2]) -bpy.context.selected_objects[0].rotation_euler[1]),
                (float(sensors[1]) -bpy.context.selected_objects[0].rotation_euler[2])]
#setup logging
logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger('run method')

#http server setup
_loop = asyncio.get_event_loop()
_httpd = _loop.create_server(lambda: httpd.HttpProtocol('192.168.0.10', 'D:\\OSC_phone-bone\\SimpleBlenderWebRemote\\BlenderRemote\\static\\'),
                               '0.0.0.0',
                               80)
#websocket setup
_wsd = websockets.serve(WebsocketRecv, '0.0.0.0', 5678)


#launching services
_logger.debug('Launching websocket daemon..')
websocket_task = asyncio.ensure_future(_wsd)
_logger.debug('Launching http daemon..')
httpd_task = asyncio.ensure_future(_httpd)

async_loop.ensure_async_loop()
