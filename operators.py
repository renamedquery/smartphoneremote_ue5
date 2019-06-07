
import logging
import gc
import os

import locale
import logging
import bpy
import sys
import mathutils
import numpy as np
import math
import socket

import bpy
import mathutils
from .arcore import ArCoreInterface, ArEventHandler

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

BLENDER  =  np.matrix([[-1, 0, 0, 0],
                      [0, 0, 1, 0],
                      [0, 1, 0, 0],
                      [ 0, 0, 0, 1]])

app = None


'''
    Utility functions
'''


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



def apply_camera(frame):
    from mathutils import Matrix

    try:
        camera = bpy.context.scene.camera
        origin = bpy.data.objects.get("root")
        if camera: 
            # cam_location = (Vector(frame.camera.translation) - Vector(frame.root.translation))*(10/frame.root.scale[0])
            # camera.location = cam_location
            # camera.rotation_quaternion = frame.camera.rotation

            # P = mathutils.Matrix(frame.camera.view_matrix.A)
            
            bpose = frame.camera.view_matrix * BLENDER 
            worigin = frame.root.world_matrix * BLENDER 
            
            # T1  =  np.matrix([[1, 0, 0, 0],
            #                 [0, 1, 0, 0],
            #                 [0, 0, 1, 0],
            #                 [ 0, 0, 0, 1]])
            # T1[3] = (bpose[3] - worigin[3])

            # R0 = worigin
            # R0[3] = [0,0,0,1]

            # T=T1
            # T[3] =  (bpose[3] - worigin[3]) * (-1)

            # R1 = bpose
            # R1[3] = [0,0,0,1]

            # pose = R1 * T1 * R0 * T
            bpose[3] = (bpose[3] - worigin[3])*(1/np.linalg.norm(worigin[1]))
            camera.matrix_world = pose.A 
            # log.info(frame.camera.view_matrix)
            # camera.translation = frame.camera.translation
            # log.info(frame.camera.view_matrix)
        
        if origin:
            pose = frame.root.world_matrix * BLENDER 
            origin.matrix_world = pose.A
    except:
        log.info("apply camera error")
        


class RemoteStartOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "remote.start"
    bl_label = "Start remote link"

    def execute(self, context):
        global app
        handler =  ArEventHandler()
    
        handler.append(apply_camera)

        app = ArCoreInterface(handler)
        app.start()

        
        return {'FINISHED'}


class RemoteStopOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "remote.stop"
    bl_label = "Stop remote link"

    def execute(self, context):
        global app

        if app:
            app.stop()
            del app
        return {'FINISHED'}


class RemoteRestartOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "remote.restart"
    bl_label = "Reboot remote link"

    def execute(self, context):
        pass
        return {'FINISHED'}


# def WebsocketRecv(websocket, path):
#     import bpy
#     print("starting websocket server on 5678")

#     _init_rotation = False
#     offset = mathutils.Quaternion()
#     while True:
#         data = await websocket.recv()
#         if 'tracking' in path:
#             if data == 'i':
#                 print("init requested")
#                 # _origin = copy.copy(bpy.context.selected_objects[0].matrix_basis)
#                 save_pose()
#                 await websocket.send("ready")
#             elif data == 's':
#                 _init_rotation = False
#             elif data[0] == 'p':

#                 sensors = data.strip('p').split('/')

#                 if _init_rotation == False:
#                     bpy.context.object.rotation_mode = 'QUATERNION'
#                     import copy
#                     if float(sensors[0]) != 0:
#                         bpy.context.object.rotation_mode = 'QUATERNION'
#                         # print("input rotation: " + str(sensors))
#                         # print("before rotation: "+str(copy.copy(bpy.context.selected_objects[0].rotation_euler)))
#                         offset = bpy.context.selected_objects[0].matrix_basis.to_quaternion(
#                         )
#                         # offset = [(float(sensors[0]) -copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.x))),
#                         #     (float(sensors[1]) - copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.y))),
#                         #     (float(sensors[2]) - copy.copy(math.degrees(bpy.context.selected_objects[0].rotation_euler.z)))]
#                         print("offset: " + str(offset))
#                         _init_rotation = True
#                 # print(_rotation)

#                  # print(str(sensors[0]))
#                 else:
#                     smartphoneRotation = mathutils.Quaternion(
#                         [float(sensors[0]), float(sensors[1]), float(sensors[2]), float(sensors[3])])
#                     # x =float(sensors[0]) - offset[0]; #(_origin.to_euler().x + float(sensors[0]))
#                     # y =float(sensors[1]) - offset[1];#(_origin.to_euler().y + float(sensors[1]))
#                     # z =float(sensors[2]) - offset[2];#(_origin.to_euler().z + float(sensors[2]))
#                     # print(str(_origin.to_euler()))
#                     #
#                     # precompute to save on processing time
#                     # cX = math.cos(x / 2)
#                     # cY = math.cos(y / 2)
#                     # cZ = math.cos(z / 2)
#                     # sX = math.sin(x / 2)
#                     # sY = math.sin(y / 2)
#                     # sZ = math.sin(z / 2)
#                     #
#                     # target_rotation = mathutils.Quaternion()
#                     # target_rotation.w = cX * cY * cZ - sX * sY * sZ
#                     # target_rotation.x = sX * cY * cZ - cX * sY * sZ
#                     # target_rotation.y = cX * sY * cZ + sX * cY * sZ
#                     # target_rotation.z = cX * cY * sZ + sX * sY * cZ
#                     #
#                     # # target_rotation = multiply_quat(smartphoneRotation,_origin.to_quaternion())

#                     # bpy.context.selected_objects[0].rotation_euler =(math.radians(x),math.radians(y),math.radians(z))#target_rotation
#                     # bpy.context.selected_objects[0].rotation_quaternion[0] = float(
#                     #     sensors[0]) + _origin.to_quaternion().w
#                     # bpy.context.selected_objects[0].rotation_quaternion[1] = float(
#                     #     sensors[1]) + _origin.to_quaternion().x
#                     # bpy.context.selected_objects[0].rotation_quaternion[2] = float(
#                     #     sensors[2]) + _origin.to_quaternion().y
#                     # bpy.context.selected_objects[0].rotation_quaternion[3] = float(
#                     #     sensors[3]) + _origin.to_quaternion().z
#                     # multiply_quat(offset,smartphoneRotation.inverted())
#                     bpy.context.selected_objects[0].rotation_quaternion = smartphoneRotation
#                     #

#         elif 'script' in path:
#             eval(data)
#         elif 'commands' in path:
#             print("init rotation")
#             sensors = data.split('/')
#             offset = [
#                 (float(sensors[3]) -
#                  bpy.context.selected_objects[0].rotation_euler[0]),
#                 (float(sensors[2]) -
#                  bpy.context.selected_objects[0].rotation_euler[1]),
#                 (float(sensors[1]) - bpy.context.selected_objects[0].rotation_euler[2])]

# def orb_worker_feed():
#     # Wait for ImageProcess
#     await asyncio.sleep(2)
#     async with websockets.connect(
#             'ws://localhost:6302/ws') as cli:

#         print("connected" + str(cli))
#         await cli.send("blender_instance_login")
#         print("done")
#         while True:
#             data = await cli.recv()

#             try:
#                 #print(data)
#                 slamTransmorm = numpy.matrix(data)
#                 P = mathutils.Matrix(slamTransmorm.A)
#                 # print(P)

#                 # print("test", sep=' ', end='n', file=sys.stdout, flush=False)
#                 # bpy.context.selected_objects[0].delta_location = mathutils.Vector((test[3,0],test[3,1],test[3,0])) #test.A. #.transpose().A
#                 #new_translation =  (bpy.context.selected_objects[0].matrix_basis.translation - mathutils.Vector((test[3,0],test[3,1],test[3,0])))
#                 # bpy.context.selected_objects[0].matrix_basis.translation = _origin.translation + mathutils.Vector(
#                     # (slamTransmorm[3, 0] * 10, slamTransmorm[3, 1] * 10, slamTransmorm[3, 2] * 10))
#                 # print(str(mathutils.Vector((test[3,0],test[3,1],test[3,2]))))

#                 # blenderTransform = mathutils.Matrix(slamTransmorm.A)
#                 #bpy.context.selected_objects[0].rotation_quaternion = mathutils.Matrix(slamTransmorm.A).to_quaternion()

#                 bpy.context.selected_objects[0].rotation_quaternion = P.to_quaternion()
#                 bpy.context.selected_objects[0].location = P.to_translation()
#                 # bpy.context.selected_objects[0].matrix_basis = origin_pose + mathutils.Matrix(test.A)
#                 # bpy.context.selected_objects[0].location = test[0:2,3]
#                 # print("translation" + str(test[0:3,3]))
#                 # bpy.context.selected_objects[0].location.x = test[3,0]
#                 # bpy.context.selected_objects[0].location.y = test[3,1]
#                 # bpy.context.selected_objects[0].location.z = test[3,2]
#                 #bpy.context.selected_objects[0].matrix_basis = slamTransmorm.A
#                 # print( bpy.data.objects['Cube'].matrix_basis)
#                 #print(bpy.data.objects['Cube'].matrix_basis )

#             except:
#                 # try:
#                 #     # if text.split()[0][0] == 'p':
#                 #     #     print("Point map buffer detected", sep=' ', end='n', file=sys.stdout, flush=False)
#                 #     #     _map.append(text.strip('[]p').split(';'))
#                 #     #     print("map state:"+ _map)
#                 #     #     #bpy.ops.object.empty_add(type='PLAIN_AXES', radius=0.1, view_align=False, location=(p[0], p[1], p[2]))
#                 #
#                 # except:
#                 pass


classes = {
    RemoteStartOperator,
    RemoteStopOperator,
    RemoteRestartOperator,
}


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    global app

    if app:
        if app.is_running():
            app.stop()
            del app 

    for cls in classes:
        unregister_class(cls)
