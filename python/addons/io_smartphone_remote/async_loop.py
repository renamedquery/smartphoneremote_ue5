# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""Manages the asyncio loop."""

import asyncio
import traceback
import concurrent.futures
import logging
import gc

import bpy

log = logging.getLogger(__name__)

# Keeps track of whether a loop-kicking operator is already running.
_loop_kicking_operator_running = False
_stop_daemons = False


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
    # loop.set_debug(True)

    # from . import pillar
    # # No more than this many Pillar calls should be made simultaneously
    # pillar.pillar_semaphore = asyncio.Semaphore(3, loop=loop)


def kick_async_loop(*args) -> bool:
    """Performs a single iteration of the asyncio event loop.

    :return: whether the asyncio loop should stop after this kick.
    """

    loop = asyncio.get_event_loop()

    # Even when we want to stop, we always need to do one more
    # 'kick' to handle task-done callbacks.
    stop_after_this_kick = False

    if loop.is_closed():
        log.warning('loop closed, stopping immediately.')
        return True

    all_tasks = asyncio.Task.all_tasks()
    if not len(all_tasks):
        # log.debug('no more scheduled tasks, stopping after this kick.')
        stop_after_this_kick = True

    elif all(task.done() for task in all_tasks):
        log.debug('all %i tasks are done, fetching results and stopping after this kick.',
                  len(all_tasks))
        stop_after_this_kick = True

        # Clean up circular references between tasks.
        gc.collect()

        for task_idx, task in enumerate(all_tasks):
            if not task.done():
                continue

            # noinspection PyBroadException
            try:
                res = task.result()
                log.debug('   task #%i: result=%r', task_idx, res)
            except asyncio.CancelledError:
                # No problem, we want to stop anyway.
                log.debug('   task #%i: cancelled', task_idx)
            except Exception:
                print('{}: resulted in exception'.format(task))
                traceback.print_exc()

            # for ref in gc.get_referrers(task):
            #     log.debug('      - referred by %s', ref)

    loop.stop()
    loop.run_forever()

    return stop_after_this_kick


def ensure_async_loop():
    log.debug('Starting asyncio loop')
    result = bpy.ops.asyncio.loop()
    log.debug('Result of starting modal operator is %r', result)


def erase_async_loop():
    global _loop_kicking_operator_running

    log.debug('Erasing async loop')

    loop = asyncio.get_event_loop()
    loop.stop()


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
        # if not _loop_kicking_operator_running:
        #     return {'FINISHED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        # self.log.debug('KICKING LOOP')
        stop_after_this_kick = kick_async_loop()


            # context.window_manager.event_timer_remove(self.timer)
            # _loop_kicking_operator_running = False
            # self.log.debug('Stopped asyncio loop kicking')
            # return {'FINISHED'}
        # if stop_after_this_kick:
        #     context.window_manager.event_timer_remove(self.timer)
        #     _loop_kicking_operator_running = False
        #
        #     self.log.debug('Stopped asyncio loop kicking')
        #     return {'FINISHED'}

        return {'RUNNING_MODAL'}





def register():
    bpy.utils.register_class(AsyncLoopModalOperator)


def unregister():
    bpy.utils.unregister_class(AsyncLoopModalOperator)
