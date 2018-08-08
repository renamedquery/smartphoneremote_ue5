
import asyncio
import traceback
import concurrent.futures
import logging
import gc

import websockets
import subprocess
import os

import logging
import httpd
import bpy
import sys
import socket
from bpy.app.handlers import persistent

import bpy

log = logging.getLogger(__name__)

# Keeps track of whether a loop-kicking operator is already running.
_loop_kicking_operator_running = False
_daemons = []
'''
    Utility functions
'''
def GetCurrentIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

'''
    control functions
'''
def setup_asyncio_executor():
    """Sets up AsyncIO to run properly on each platform."""

    import sys

    if sys.platform == 'win32':
        asyncio.get_event_loop().close()
        # On Windows, the default event loop is SelectorEventLoop, which does
        # not support subprocesses. ProactorEventLoop should be used instead.
        # Source: https://docs.python.org/3/library/asyncio-subprocess.html
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop.set_default_executor(executor)

@persistent
def auto_launch_daemons(scene):
    log.debug('Auto launch smartphone remote daemon')
    setup_daemons()
    run_daemons()
    log.debug('Done.')

def run_daemons():
    log.debug('Starting  smartphone remote daemon')
    bpy.context.user_preferences.inputs.srDaemonRunning[1]['default'] = True
    result = bpy.ops.asyncio.loop()
    log.debug('Result of starting modal operator is %r', result)

def stop_daemons():
    global _loop_kicking_operator_running

    if bpy.context.user_preferences.inputs.srDaemonRunning[1]['default']:
        log.debug('Stopping')
        for i in _daemons:
            i.cancel()
        _daemons.clear()
        bpy.context.user_preferences.inputs.srDaemonRunning[1]['default'] = False
        _loop_kicking_operator_running = False
        loop = asyncio.get_event_loop()
        loop.stop()
    else:
        pass

def setup_daemons():
    logging.basicConfig(level=logging.INFO)

    _ip = GetCurrentIp()


    if sys.platform == "win32":
        _loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(_loop)
    else:
        _loop = asyncio.get_event_loop()

    try:
        setup_asyncio_executor()

        print("async_loop setuping")
    except:
        print("async_loop already setup")
        pass

    root = os.path.dirname(os.path.abspath(__file__))+"/static"
    print("launch server on " + _ip+ root)
    _httpd = _loop.create_server(lambda: httpd.HttpProtocol(_ip, root),
                                 '0.0.0.0',
                                 8080)

    _wsd = websockets.serve(WebsocketRecv, '0.0.0.0', 5678)

    websocket_task = asyncio.ensure_future(_wsd)
    # httpd_task = _loop.run_until_complete(_httpd)
    httpd_task = asyncio.ensure_future(_httpd)

    _daemons.append(websocket_task)
    _daemons.append(httpd_task)
    camera_task = asyncio.ensure_future(get_frame(_loop))
    camera_feed_task = asyncio.ensure_future(CameraFeed())


    #_loop.run_forever()
    bpy.app.handlers.load_post.clear()

class StopBlenderRemote(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.stop_blender_remote"
    bl_label = "Stop daemons"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        stop_daemons()
        return {'FINISHED'}

class RestartBlenderRemote(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.restart_blender_remote"
    bl_label = "Reboot daemons"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        stop_daemons()
        setup_daemons()
        run_daemons()
        return {'FINISHED'}

class AsyncLoopModalOperator(bpy.types.Operator):
    bl_idname = 'asyncio.loop'
    bl_label = 'Runs the asyncio main loop'

    timer = None
    log = logging.getLogger(__name__ + '.AsyncLoopModalOperator')

    def __del__(self):
        global _loop_kicking_operator_running

        # This can be required when the operator is running while Blender
        # (re)loads a file. The operator then doesn't get the chance to
        # finish the async tasks, hence stop_after_this_kick is never True.
        _loop_kicking_operator_running = False

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        global _loop_kicking_operator_running

        if _loop_kicking_operator_running:
            self.log.debug('Another loop-kicking operator is already running.')
            return {'PASS_THROUGH'}

        context.window_manager.modal_handler_add(self)
        _loop_kicking_operator_running = True

        wm = context.window_manager
        self.timer = wm.event_timer_add(0.00001, context.window)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global _loop_kicking_operator_running

        # If _loop_kicking_operator_running is set to False, someone called
        # erase_async_loop(). This is a signal that we really should stop
        # running.
        if not _loop_kicking_operator_running:
            context.window_manager.event_timer_remove(self.timer)
            return {'FINISHED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        loop = asyncio.get_event_loop()
        loop.stop()
        loop.run_forever()

        if bpy.context.user_preferences.inputs.srDaemonRunning[1]['default'] == False:
            context.window_manager.event_timer_remove(self.timer)
            _loop_kicking_operator_running = False
            self.log.debug('Stopped asyncio loop kicking')
            return {'FINISHED'}


        return {'RUNNING_MODAL'}

class CameraProcessProtocol(asyncio.SubprocessProtocol):
    def __init__(self, exit_future):
        self.exit_future = exit_future
        self.output = bytearray()

    def pipe_data_received(self, fd, data):
        text = data.decode(locale.getpreferredencoding(False))
        pose = mathutils.Matrix()

        try:
            test = numpy.matrix(text)
            test[0:2,3]*=10

            '''for x in range(0,3):
                for y in range(0,3):
                   pose[x][y] = test[x,y]'''

            bpy.data.objects['Cube'].matrix_basis = test.transpose().A
            print( bpy.data.objects['Cube'].matrix_basis)
            #print(bpy.data.objects['Cube'].matrix_basis )
            #bpy.data.objects['Cube'].location.y = test[0,3]*10
            #bpy.data.objects['Cube'].location.z = test[1,3]*10
            #bpy.data.objects['Cube'].location.x = test[2,3]*10
            #bpy.data.objects['Cube'].matrix_world = pose * bpy.data.objects['Cube'].matrix_world
            #print("Translation:"+test[0,3]*10+" - "+test[1,3]*10+" - "+test[2,3]*10)

            #print(pose.rotation)
        except:
            print("matrix parsing none")
            pass
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
    offset = [0.0, 0.0, 0.0,0.0]
    while True:
        data = await websocket.recv()
        # print(data)
        if 'tracking' in path:
            sensors = data.split('/')
            bpy.context.object.rotation_mode = 'QUATERNION'

            bpy.context.selected_objects[0].rotation_quaternion[0] = float(
                sensors[0])
            bpy.context.selected_objects[0].rotation_quaternion[1] = float(
                sensors[1])
            bpy.context.selected_objects[0].rotation_quaternion[2] = float(
                sensors[2])
            bpy.context.selected_objects[0].rotation_quaternion[3] = float(
                sensors[3])
        elif 'script' in path:
            eval(data)
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

def register():
    bpy.utils.register_class(StopBlenderRemote)
    bpy.utils.register_class(RestartBlenderRemote)
    bpy.utils.register_class(AsyncLoopModalOperator)
    bpy.app.handlers.load_post.append(auto_launch_daemons)


def unregister():
    bpy.utils.unregister_class(StopBlenderRemote)
    bpy.utils.unregister_class(RestartBlenderRemote)
    bpy.utils.unregister_class(AsyncLoopModalOperator)
    bpy.app.handlers.load_post.clear()
    print('test', sep=' ', end='n', file=sys.stdout, flush=False)
