
import logging
import gc
import os
import umsgpack

import locale
import logging
import bpy
import sys
import mathutils
import numpy as np
import math
import socket
import json
import bpy
import mathutils
from .arcore import ArCoreInterface, ArEventHandler
import queue


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

TASKS_FREQUENCY = .5
SCENE_CACHE = "cache.glb"
BLENDER = np.matrix([[-1, 0, 0, 0],
                     [0, 0, 1, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1]])

app = None
app_ctx = None
execution_queue = queue.Queue()
execution_result_queue = queue.Queue()

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
   Camera managment
'''
def apply_camera(frame):
    from mathutils import Matrix

    try:
        camera = bpy.context.scene.camera
        
        if camera:
            # cam_location = (Vector(frame.camera.translation) - Vector(frame.root.translation))*(10/frame.root.scale[0])
            # camera.location = cam_location
            # camera.rotation_quaternion = frame.camera.rotation

            # P = mathutils.Matrix(frame.camera.view_matrix.A)


            bpose = frame.camera.view_matrix * BLENDER
            worigin = frame.root.world_matrix * BLENDER

            # T1  =  np.matrix([[1.0, 0.0, 0.0, 0.0],
            #                     [0.0, 1.0, 0.0, 0.0],
            #                     [0.0, 0.0, 1.0, 0.0],
            #                     [ 0.0, 0.0, 0.0, 1.0]])
            # T1[3] = (bpose[3] - worigin[3])

            # R0 = worigin

            # T=T1
            # T[3] =  (bpose[3] - worigin[3]) * (-1)

            # R1 = bpose
            # R1[3] = [0,0,0,1]

            # pose = R1 * T1 * R0  * T
            bpose[3] = (bpose[3] - worigin[3])*(1/np.linalg.norm(worigin[1]))
            camera.matrix_world = bpose.A
            # log.info(frame.camera.view_matrix)
            # camera.translation = frame.camera.translation
            # log.info(frame.camera.view_matrix)

    except:
        log.info("apply camera error")

def record_camera():
    global app_ctx        
    import bpy

    # Create and setup new action
    new_action =  bpy.data.actions.new("camera_0")
    bpy.data.scenes[0].camera.animation_data_create()
    bpy.data.scenes[0].camera.animation_data.action = new_action

    # Launch record 
    bpy.data.scenes[0].tool_settings.use_keyframe_insert_auto = True
    bpy.ops.screen.animation_play(app_ctx)
    


'''
   Scene export
'''

def export_cached_scene():
    bpy.ops.export_scene.gltf(
        export_format='GLB',
        ui_tab='GENERAL',
        export_copyright="",
        export_image_format='NAME',
        export_texcoords=True,
        export_normals=True,
        export_draco_mesh_compression_enable=False,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
        export_tangents=False,
        export_materials=True,
        export_colors=True,
        export_cameras=False,
        export_selected=False,
        export_extras=False,
        export_yup=True,
        export_apply=False,
        export_animations=True,
        export_frame_range=True,
        export_frame_step=1,
        export_force_sampling=False,
        export_current_frame=False,
        export_skins=True,
        export_all_influences=False,
        export_morph=True,
        export_morph_normal=True,
        export_morph_tangent=False,
        export_lights=True,
        export_displacement=False,
        will_save_settings=False,
        filepath=SCENE_CACHE,
        check_existing=True,
        filter_glob="*.glb;*.gltf"
    )


def get_cached_scene():
    file = open(SCENE_CACHE, "rb")

    return file.read()


class RemoteStartOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "remote.start"
    bl_label = "Start remote link"

    def execute(self, context):
        global app
        handler = ArEventHandler()

        # generate scene cache
        export_cached_scene()

        # Arcore interface setup
        handler.bindOnFrameReceived(apply_camera)
        handler.bindGetScene(get_cached_scene)
        handler.bindRecord(record_camera)

        app = ArCoreInterface(handler)
        app.start()

        global app_ctx

        app_ctx = context.copy()

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
