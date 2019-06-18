
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
import json
import bpy
import mathutils
from .arcore import ArCoreInterface, ArEventHandler
import queue
from mathutils import Matrix, Vector

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

TASKS_FREQUENCY = .0001
SCENE_CACHE = "scene_cache.glb"
BLENDER = np.matrix([[-1, 0, 0, 0],
                     [0, 0, 1, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1]])

app = None
is_recording = False
execution_queue = queue.Queue()
execution_result_queue = queue.Queue()
stop_modal_executor = False

'''
    Utility functions
'''

def GetCurrentIp():
    """
    Retrieve the main network interface IP.

    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def getContext():
    """
    Load the current blender context and fill it 
    with missing informations.
    """
    log.info("getContext()")
    import bpy
    
    override = bpy.context.copy()
       
                
    return override
    

def run_in_main_thread(function, args=None):
    """
    Queue a function in order to run it 
    into the blender main thread.
    
    
    """
    execution_queue.put((function,args))
    
    return execution_result_queue.get()


def execute_queued_functions():
    """
    Execute queued functions into the blender main thread.
    """
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
        execution_result_queue.put("done")

    return 1.0


'''
   Camera managment
'''
def apply_ar_frame(frame):
    run_in_main_thread(apply_camera,frame)


def apply_camera(frame):
    """Apply frame camera pose into blender scene active camera

        TODO: load camera intrinsec    
    """
    global is_recording
    try:
        camera = bpy.context.scene.camera
        
        if camera:
            

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
            
            if is_recording:
                camera.keyframe_insert(data_path="location")
                camera.keyframe_insert(data_path="rotation_quaternion")
           

            # log.info(frame.camera.view_matrix)
            # camera.translation = frame.camera.translation
            # log.info(frame.camera.view_matrix)
            
    except Exception as e:
        log.info("apply camera error: {}".format(e))


def setup_camera_animation():
    global is_recording
    ctx = getContext()
    scene = ctx["scene"]

    # Create and setup new action
    scene.camera.rotation_mode = 'QUATERNION'

    new_action =  bpy.data.actions.new("camera_0")
    scene.camera.animation_data_create()
    scene.camera.animation_data.action = new_action

    # Launch record 
    bpy.ops.screen.animation_play(ctx)
    is_recording = True


def stop_camera_animation():
    global is_recording

    bpy.ops.screen.animation_cancel()
    bpy.context.scene.frame_current = 1
    is_recording = False


def update_camera_animation():
    global is_recording
    import bpy

    ctx = getContext().copy()
    
    if is_recording:
        return ctx['scene'].frame_current
    else:
        return "STOPPED"

def record_camera(status):
    """
    Record camera animation callback.

    TODO: Record config
    """      
    log.info(status)
    blender_state = "NONE"
    if status == "START":
        run_in_main_thread(setup_camera_animation)
        blender_state = "STARTED"
    elif status == "STATE":
        blender_state = str(run_in_main_thread(update_camera_animation))
        log.info(str(blender_state))
    elif status == "STOP":
        run_in_main_thread(stop_camera_animation)
        blender_state = "STOPPED"


    return blender_state



'''
   Scene export
'''

def export_cached_scene():
    """
    Export the current scene to SCENE_CACHE
    
    TODO: export config
    """


    bpy.ops.export_scene.gltf(
        getContext(),
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
        export_apply=True,
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
        export_lights=False,
        export_displacement=False,
        will_save_settings=False,
        filepath=SCENE_CACHE,
        check_existing=True,
        filter_glob="*.glb;*.gltf"
    )


def get_cached_scene(offset,chunk_size):
    """
    Export the scene and return the cache file stream.
    """

    # STEP 0: Export the scene 
    if offset == 0:
        log.info("export the scene...")
        run_in_main_thread(export_cached_scene)
        file = open(SCENE_CACHE, "rb")
        log.info("Done, exported  {} bytes".format(len(file.read())))
        file.close()



    # STEP 1: Read chunk of data from file
    log.info("open : {}".format(SCENE_CACHE))
    file = open(SCENE_CACHE, "rb")
    file.seek(offset, os.SEEK_SET)
    data = file.read(chunk_size)

    log.info("read : {}".format(offset))

    # file = open(SCENE_CACHE, "rb")

    return data


'''
    Handlers
'''
def record(scene):
    global is_recording

    if is_recording:
        if scene.frame_current == (scene.frame_end-1):
            stop_camera_animation()

            

'''
   Operators
'''

class RemoteStartOperator(bpy.types.Operator):
    """Start the blender remote"""
    bl_idname = "remote.start"
    bl_label = "Start remote link"

    def execute(self, context):
        global app
        handler = ArEventHandler()      

        # Arcore interface setup
        handler.bindOnFrameReceived(apply_ar_frame)
        handler.bindGetScene(get_cached_scene)
        handler.bindRecord(record_camera)

        app = ArCoreInterface(handler)
        app.start()

        bpy.ops.wm.modal_executor_operator()
        bpy.app.handlers.frame_change_post.append(record)


        return {'FINISHED'}


class RemoteStopOperator(bpy.types.Operator):
    """Stop the remote daemon"""
    bl_idname = "remote.stop"
    bl_label = "Stop remote link"

    def execute(self, context):
        global app, stop_modal_executor

        if app:
            app.stop()
            del app

        stop_modal_executor = True
        bpy.app.handlers.frame_change_post.remove(record)
        # bpy.app.timers.unregister(execute_queued_functions)

        return {'FINISHED'}


class RemoteRestartOperator(bpy.types.Operator):
    """Reboot the remote daemon"""
    bl_idname = "remote.restart"
    bl_label = "Reboot remote link"

    def execute(self, context):
        pass
        return {'FINISHED'}


class RemoteModalExecutorOperator(bpy.types.Operator):
    """Modal operator used to execute tasks that required a VALID context (like operators)"""
    bl_idname = "wm.modal_executor_operator"
    bl_label = "Modal Executor Operator"

    _timer = None

    def modal(self, context, event):
        global stop_modal_executor, execution_queue

        if stop_modal_executor:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if not execution_queue.empty():
                function,args = execution_queue.get()

                if args:
                    result = function(args)
                else:
                    result = function()
                
                if result:
                    execution_result_queue.put(result)
                else:
                    execution_result_queue.put("done")
            

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(TASKS_FREQUENCY, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

classes = {
    RemoteStartOperator,
    RemoteStopOperator,
    RemoteRestartOperator,
    RemoteModalExecutorOperator,
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
