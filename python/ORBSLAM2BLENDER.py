import asyncio
import sys
import async_loop
import contextlib
import os
import locale
import numpy
import bpy
import mathutils

class DataProtocol(asyncio.SubprocessProtocol):
    def __init__(self, exit_future):
        self.exit_future = exit_future
        self.output = bytearray()

    def pipe_data_received(self, fd, data):
        text = data.decode(locale.getpreferredencoding(False))
        pose = mathutils.Matrix()
        
        try:
            buffer = numpy.matrix(text)
            buffer[0:2,3]*=10            
            bpy.data.objects['Camera'].matrix_basis = buffer.transpose().A
            print( bpy.data.objects['Camera'].matrix_basis)
        except:   
            print("matrix parsing none")
            pass       
        
        self.output.extend(data)

    def process_exited(self):
        print("process exited")
        self.exit_future.set_result(True)

@asyncio.coroutine
def get_data(loop):
    exit_future = asyncio.Future(loop=loop)

    # Create the subprocess controlled by the protocol DateProtocol,
    # redirect the standard output into a pipe
    create = loop.subprocess_exec(lambda: DataProtocol(exit_future),
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


try:
    async_loop.setup_asyncio_executor()
    async_loop.register()
    print("async_loop setuping")
except:
    print("async_loop already setup")
    pass


if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()


date = asyncio.ensure_future(get_data(loop))
async_loop.ensure_async_loop()

