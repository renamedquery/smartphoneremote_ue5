
import asyncio
import traceback
import concurrent.futures
import logging
import gc

import websockets
import subprocess
import os

import locale
import logging
import httpd
import bpy
import sys
import socket
import mathutils
import numpy
import math
from bpy.app.handlers import persistent

import bpy

log = logging.getLogger(__name__)

# Keeps track of whether a loop-kicking operator is already running.
_loop_kicking_operator_running = False
_daemons = []
_map = []
_rotation = []
_origins = []
_origin = mathutils.Matrix()

# _base = Matrix([[1,0,0],[0,0,1],[0,-1,0],[0,0,0]])
# _dest = = Matrix([[0,1,0],[0,0,1],[-1,0,0],[0,0,0]])
'''
    Utility functions
'''


def save_pose():
    import copy

    print("saving relative pose matrix")
    global _origin
    _origin = copy.copy(bpy.context.selected_objects[0].matrix_basis)
    print(str(_origin))
    # for o in bpy.data.objects:
    #     # t=
    #     _origins.append((o.name,copy.copy(o.matrix_basis)))


def GetCurrentIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def multiply_quat(q, r):
    result = mathutils.Quaternion()

    result.w = (r.w * q.w - r.x * q.x - r.y * q.y - r.z * q.z)
    result.x = (r.w * q.x + r.x * q.w - r.y * q.z + r.z * q.y)
    result.y = (r.w * q.y + r.x * q.z + r.y * q.w - r.z * q.x)
    result.z = (r.w * q.z - r.x * q.y + r.y * q.x + r.z * q.w)

    return result


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


def kill_daemons():
    for i in _daemons:
        # UGLY, TODO: add better process managment
        try:
            print("cancelling " + str(i))
            i.cancel()
        except:
            try:
                print("killing child process" + str(i))
                i.kill()
            except:
                print("no process to kill", sep=' ',
                      end='n', file=sys.stdout, flush=False)

    _daemons.clear()


def check_daemons(scene):
    print("caca", sep=' ', end='n', file=sys.stdout, flush=False)


@persistent
def auto_launch_daemons(scene):
    print('Auto launch smartphone remote daemon')
    if bpy.context.user_preferences.inputs.srDaemonRunning[1]['default']:
        stop_daemons()
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
        kill_daemons()
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

    root = os.path.dirname(os.path.abspath(__file__)) + "/static"
    print("launch server on " + _ip + root)
    _httpd = _loop.create_server(lambda: httpd.HttpProtocol(_ip, root),
                                 '0.0.0.0',
                                 8080)

    _wsd = websockets.serve(WebsocketRecv, '0.0.0.0', 5678)

    websocket_task = asyncio.ensure_future(_wsd)
    httpd_task = asyncio.ensure_future(_httpd)
    orb_task = asyncio.ensure_future(orb_worker_feed())
    tracking_task = asyncio.ensure_future(slam_worker())

    _daemons.append(orb_task)
    _daemons.append(websocket_task)
    _daemons.append(httpd_task)
    _daemons.append(tracking_task)

    # _loop.run_forever()
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
        # BLENDER2.8
        self.timer = wm.event_timer_add(0.00001, window=context.window)

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


async def slam_worker():
    # Create the subprocess, redirect the standard output into a pipe
    proc = await asyncio.create_subprocess_exec('/home/slumber/Repos/DeviceTracking/build/DeviceTracking',
                                                stdout=asyncio.subprocess.PIPE)

    _daemons.append(proc)
    # Read one line of output
    data = await proc.stdout.readline()
    line = data.decode('ascii').rstrip()

    # Wait for the subprocess exit
    await proc.wait()
    print(line)
    return line


async def WebsocketRecv(websocket, path):
    import bpy
    print("starting websocket server on 5678")

    _init_rotation = False
    offset = mathutils.Quaternion()
    while True:
        data = await websocket.recv()
        if 'tracking' in path:
            if data == 'i':
                print("init requested")
                # _origin = copy.copy(bpy.context.selected_objects[0].matrix_basis)
                save_pose()
                await websocket.send("ready")
            elif data == 's':
                _init_rotation = False
            elif data[0] == 'p':

                sensors = data.strip('p').split('/')

                if _init_rotation == False:
                    bpy.context.object.rotation_mode = 'QUATERNION'
                    import copy
                    if float(sensors[0]) != 0:
                        bpy.context.object.rotation_mode = 'QUATERNION'
                        # print("input rotation: " + str(sensors))
                        # print("before rotation: "+str(copy.copy(bpy.context.selected_objects[0].rotation_euler)))
                        offset = bpy.context.selected_objects[0].matrix_basis.to_quaternion(
                        )
                        # offset = [(float(sensors[0]) -copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.x))),
                        #     (float(sensors[1]) - copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.y))),
                        #     (float(sensors[2]) - copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.z)))]
                        print("offset: " + str(offset))
                        _init_rotation = True
                # print(_rotation)

                 # print(str(sensors[0]))
                else:
                    smartphoneRotation = mathutils.Quaternion(
                        [float(sensors[0]), float(sensors[1]), float(sensors[2]), float(sensors[3])])
                    # x =float(sensors[0]) - offset[0]; #(_origin.to_euler().x + float(sensors[0]))
                    # y =float(sensors[1]) - offset[1];#(_origin.to_euler().y + float(sensors[1]))
                    # z =float(sensors[2]) - offset[2];#(_origin.to_euler().z + float(sensors[2]))
                    # print(str(_origin.to_euler()))
                    #
                    # precompute to save on processing time
                    # cX = math.cos(x / 2)
                    # cY = math.cos(y / 2)
                    # cZ = math.cos(z / 2)
                    # sX = math.sin(x / 2)
                    # sY = math.sin(y / 2)
                    # sZ = math.sin(z / 2)
                    #
                    # target_rotation = mathutils.Quaternion()
                    # target_rotation.w = cX * cY * cZ - sX * sY * sZ
                    # target_rotation.x = sX * cY * cZ - cX * sY * sZ
                    # target_rotation.y = cX * sY * cZ + sX * cY * sZ
                    # target_rotation.z = cX * cY * sZ + sX * sY * cZ
                    #
                    # # target_rotation = multiply_quat(smartphoneRotation,_origin.to_quaternion())

                    # bpy.context.selected_objects[0].rotation_euler =(math.radians(x),math.radians(y),math.radians(z))#target_rotation
                    # bpy.context.selected_objects[0].rotation_quaternion[0] = float(
                    #     sensors[0]) + _origin.to_quaternion().w
                    # bpy.context.selected_objects[0].rotation_quaternion[1] = float(
                    #     sensors[1]) + _origin.to_quaternion().x
                    # bpy.context.selected_objects[0].rotation_quaternion[2] = float(
                    #     sensors[2]) + _origin.to_quaternion().y
                    # bpy.context.selected_objects[0].rotation_quaternion[3] = float(
                    #     sensors[3]) + _origin.to_quaternion().z
                    # multiply_quat(offset,smartphoneRotation.inverted())
                    bpy.context.selected_objects[0].rotation_quaternion = smartphoneRotation
                    #

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


async def orb_worker_feed():
    # Wait for ImageProcess
    await asyncio.sleep(2)
    async with websockets.connect(
            'ws://localhost:6302/ws') as cli:

        print("connected" + str(cli))
        await cli.send("blender_instance_login")
        print("done")
        while True:
            data = await cli.recv()

            try:
                print(data)
                slamTransmorm = numpy.matrix(data)

                # print("test", sep=' ', end='n', file=sys.stdout, flush=False)
                # bpy.context.selected_objects[0].delta_location = mathutils.Vector((test[3,0],test[3,1],test[3,0])) #test.A. #.transpose().A
                #new_translation =  (bpy.context.selected_objects[0].matrix_basis.translation - mathutils.Vector((test[3,0],test[3,1],test[3,0])))
                bpy.context.selected_objects[0].matrix_basis.translation = _origin.translation + mathutils.Vector(
                    (slamTransmorm[3, 0] * 10, slamTransmorm[3, 1] * 10, slamTransmorm[3, 2] * 10))
                # print(str(mathutils.Vector((test[3,0],test[3,1],test[3,2]))))

                # blenderTransform = mathutils.Matrix(slamTransmorm.A)
                #bpy.context.selected_objects[0].rotation_quaternion = mathutils.Matrix(slamTransmorm.A).to_quaternion()

                # bpy.context.selected_objects[0].matrix_basis = mathutils.Matrix(slamTransmorm.A)
                # bpy.context.selected_objects[0].matrix_basis = origin_pose + mathutils.Matrix(test.A)
                # bpy.context.selected_objects[0].location = test[0:2,3]
                # print("translation" + str(test[0:3,3]))
                # bpy.context.selected_objects[0].location.x = test[3,0]
                # bpy.context.selected_objects[0].location.y = test[3,1]
                # bpy.context.selected_objects[0].location.z = test[3,2]
                #bpy.context.selected_objects[0].matrix_basis = slamTransmorm.A
                # print( bpy.data.objects['Cube'].matrix_basis)
                #print(bpy.data.objects['Cube'].matrix_basis )

            except:
                # try:
                #     # if text.split()[0][0] == 'p':
                #     #     print("Point map buffer detected", sep=' ', end='n', file=sys.stdout, flush=False)
                #     #     _map.append(text.strip('[]p').split(';'))
                #     #     print("map state:"+ _map)
                #     #     #bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.1, view_align=False, location=(p[0], p[1], p[2]))
                #
                # except:
                pass


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
