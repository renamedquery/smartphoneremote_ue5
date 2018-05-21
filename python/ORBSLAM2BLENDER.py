import asyncio
import sys
import async_loop
import contextlib
import os
import locale
import numpy
import bpy
import mathutils
import loggin

class DateProtocol(asyncio.SubprocessProtocol):
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
def get_date(loop):
    code = 'import datetime; print(datetime.datetime.now())'
    exit_future = asyncio.Future(loop=loop)

    # Create the subprocess controlled by the protocol DateProtocol,
    # redirect the standard output into a pipe
    create = loop.subprocess_exec(lambda: DateProtocol(exit_future),
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

logging.basicConfig(level=logging.DEBUG)

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


date = asyncio.ensure_future(get_date(loop))
async_loop.ensure_async_loop()

