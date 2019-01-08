
import asyncio
import concurrent.futures
import logging
import bpy
from bpy.props import BoolProperty

log = logging.getLogger(__name__)
_loop_kicking_operator_running = False


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


class AsyncStopModalOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "asyncio.stop"
    bl_label = "Stop the asyncio main loop"

    def execute(self, context):
        global _loop_kicking_operator_running
        _loop_kicking_operator_running = False
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

        return {'RUNNING_MODAL'}


def register():
    setup_asyncio_executor()
    bpy.utils.register_class(AsyncLoopModalOperator)
    bpy.utils.register_class(AsyncStopModalOperator)


def unregister():
    bpy.utils.unregister_class(AsyncLoopModalOperator)
    bpy.utils.unregister_class(AsyncStopModalOperator)


if __name__ == '__main__':
    register()
