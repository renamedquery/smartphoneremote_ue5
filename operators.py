# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


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
import json
import bpy
import mathutils
from .arcore import ArCoreInterface, ArEventHandler
from . import environment, preference
import queue
from mathutils import Matrix, Vector

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

TASKS_FREQUENCY = .0001

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


'''
   Camera managment
'''
def apply_ar_frame(frame):
    if frame.mode == "CAMERA":
        run_in_main_thread(apply_camera_pose,frame)
    if frame.mode == "OBJECT":
         run_in_main_thread(apply_object_pose,frame)

def apply_object_pose(frame):
    """Apply frame blender pose into blender select object"""
    global is_recording

    try:
        active_object = bpy.context.object

        if active_object:

            bpose = frame.camera.view_matrix * BLENDER
            worigin = frame.root.world_matrix * BLENDER
            bpose[3] = (bpose[3] - worigin[3])*(1/np.linalg.norm(worigin[1]))

            active_object.matrix_world = bpose.A

    except Exception as e:
        log.error(e)

def normalize(_d, to_sum=True, copy=True):
    # d is a (n x dimension) np array
    d = _d if not copy else np.copy(_d)
    d -= np.min(d, axis=0)
    d /= (np.sum(d, axis=0) if to_sum else np.ptp(d, axis=0))
    return d

def normalized(a, axis=-1, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2==0] = 1
    return a / np.expand_dims(l2, axis)

def apply_camera_pose(frame):
    """Apply frame camera pose into blender scene active camera"""
    global is_recording
    '''try:
        camera = bpy.context.scene.camera
        
        if camera:
            bpose = frame.camera.view_matrix * BLENDER
            worigin = frame.root.world_matrix * BLENDER
            
            bpose[3] = (bpose[3] - worigin[3])*(1/np.linalg.norm(worigin[1]))

            camera.matrix_world = bpose.A
            camera.data.angle = frame.camera.intrinsics[0]
            
            if is_recording:
                camera.keyframe_insert(data_path="location")
                camera.keyframe_insert(data_path="rotation_quaternion")

           
    except Exception as e:
        log.info("apply camera error: {}".format(e))'''


def setup_camera_animation():
    global is_recording
    ctx = getContext()
    scene = ctx["scene"]

    # Create and setup new action
    scene.camera.rotation_mode = 'QUATERNION'

    new_action = bpy.data.actions.new("camera_0")
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
    prefs = preference.get()
    bpy.ops.export_scene.obj(
        getContext(),
        filepath=os.path.join(prefs.cache_directory,
                            environment.SCENE_FILE),
        check_existing=True,
        filter_glob="*.obj;*.mtl",
        use_selection=False,
        use_animation=False,
        use_mesh_modifiers=True,
        use_edges=True,
        use_smooth_groups=False,
        use_smooth_groups_bitflags=False,
        use_normals=True,
        use_uvs=True,
        use_materials=False,
        use_triangles=False,
        use_nurbs=False,
        use_vertex_groups=False,
        use_blen_objects=True,
        group_by_object=False,
        group_by_material=False,
        keep_vertex_order=False,
        global_scale=1,
        path_mode='AUTO',
        axis_forward='-Z',
        axis_up='Y')


def get_cached_scene(offset, chunk_size):
    """
    Export the scene and return the cache file stream.
    """
    prefs = preference.get()
    scene_filepath = os.path.join(prefs.cache_directory,
                            environment.SCENE_FILE)
    # STEP 0: Export the scene 
    if offset == 0:
        log.info("export the scene...")
        run_in_main_thread(export_cached_scene)
        file = open(scene_filepath, "rb")
        log.info("Done, exported  {} bytes".format(len(file.read())))
        file.close()

    # STEP 1: Read chunk of data from file
    log.info("open : {}".format(scene_filepath))
    file = open(scene_filepath, "rb")
    file.seek(offset, os.SEEK_SET)
    data = file.read(chunk_size)

    log.info("read : {}".format(offset))

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

        prefs = preference.get()
        handler = ArEventHandler()      

        # Arcore interface setup
        #handler.bindOnFrameReceived(apply_ar_frame)
        #handler.bindGetScene(get_cached_scene)
        #handler.bindRecord(record_camera)

        app = ArCoreInterface(handler,port=prefs.port)
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
            app = None

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
            stop_modal_executor = False
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if not execution_queue.empty():
                function, args = execution_queue.get()

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
        self._timer = wm.event_timer_add(
            TASKS_FREQUENCY, window=context.window)
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
