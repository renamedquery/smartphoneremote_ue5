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

import zmq
import msgpack
import numpy as np

import threading
import logging
import time

from . import environment

TIMEOUT = 1

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Camera():
    """ ARCore camera

    """
    def __init__(self,intrinsics=[0,0], vm=None):

        self.intrinsics = intrinsics
        if vm:
            self.view_matrix =  np.matrix([[vm[0],vm[1],vm[2],vm[3]],
                                        [vm[4],vm[5],vm[6],vm[7]],
                                        [vm[8],vm[9],vm[10],vm[11]],
                                        [vm[12],vm[13],vm[14],vm[15]]])
        else:
            self.view_matrix = np.matrix(np.zeros((4, 4)))


class Node():
    """Sceneform Node

    """
    
    def __init__(self, wm = None):
        if wm:
            self.world_matrix =  np.matrix([[wm[0],wm[1],wm[2],wm[3]],
                                        [wm[4],wm[5],wm[6],wm[7]],
                                        [wm[8],wm[9],wm[10],wm[11]],
                                        [wm[12],wm[13],wm[14],wm[15]]])
        else:
            self.world_matrix = np.matrix(np.zeros((4, 4)))


class Frame():
    """ ARCore frame

    """
    def __init__(self, camera = Camera(),root = Node()):
        self.camera = camera
        self.root = root
        self.mode = 'CAMERA'

    @classmethod
    def recv(cls,socket):
        frame_buffer = socket.recv_multipart()
        frame = Frame()

        while len(frame_buffer)>0:
            header =  frame_buffer.pop(0)
            if header == b"STATE":
                frame.mode = frame_buffer.pop(0).decode()    

            elif header == b"CAMERA":
                arCamera = Camera(
                    intrinsics=msgpack.unpackb(frame_buffer.pop(0)),
                    vm=msgpack.unpackb(frame_buffer.pop(0))
                    )

                frame.camera = arCamera
            elif header == b"NODE":
                arNode = Node(
                    wm=msgpack.unpackb(frame_buffer.pop(0))
                    )
                frame.root = arNode

        return frame


class ArEventHandler():
    """ Application Event handler

    Used to link Android Application event with 
    the local application(ex: blender).  
    """
    def __init__(self):
        self._frameListeners = []
        self._getScene = None
        self._record = None

    def bindOnFrameReceived(self,f):
        self._frameListeners.append(f)

    def bindGetScene(self, f):
        self._getScene = f

    def bindRecord(self, f):
        self._record = f

    def OnFrameReceived(self, frame):
        for f in self._frameListeners:
            f(frame)

    def OnRecord(self, status):
        if self._record:
            return self._record(status)
        else:
            log.info("Record not implemented")
            return None

    def OnGetScene(self,offset,chunk_size):
        if self._getScene:
            return self._getScene(offset,chunk_size)
        else:
            raise Exception('GetScene not implemented !')


class ArCoreInterface(object):
    """ Application Ar interface

    Interface in charge to manage the network bridge 
    between local application and the remote app.
    """
    def __init__(self, handler, port=63150):
        self._net_link = AppLink(handler, port=port)
        self.handler = handler

    def start(self):
        self._net_link.start()

    def is_running(self):
        return self._net_link.is_alive()

    def stop(self):
        self._net_link.stop()


class AppLink(threading.Thread):
    """ Application network link

    Thread use to listen android remote application.

    TODO: complete this area

    """
    def __init__(
            self,
            handler,
            port=63150,
            context=zmq.Context.instance(),
            name="Applink"):

        threading.Thread.__init__(self)
        self.name = name
        self.status = 0  # 0: idle, 1: Connecting, 2: Connected
        self.context = context
        
        # The command socket handle asynchonous commands
        # the from android application
        self.command_socket = self.context.socket(zmq.ROUTER)
        self.command_socket.setsockopt(zmq.IDENTITY, b'SERVER')
        self.command_socket.setsockopt(zmq.RCVHWM, 0)   
        self.command_socket.bind("tcp://*:{}".format(port+2))

        # Data socket is used load each frame ARCore state from 
        # the android application 
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.bind("tcp://*:{}".format(port+1))
        self.data_socket.linger = 0
        
        # TTL socket is in charge of the connexion monitoring 
        self.ttl_socket = self.context.socket(zmq.ROUTER)
        self.ttl_socket.setsockopt(zmq.IDENTITY, b'SERVERTTL')
        self.ttl_socket.setsockopt(zmq.RCVHWM, 0)   
        self.ttl_socket.linger = 0
        self.ttl_socket.bind("tcp://*:{}".format(port))

        self.client_addr = None

        self.exit_event = threading.Event()
        self.handler = handler


    def run(self):
        log.debug("Running App link")

        poller = zmq.Poller()
        poller.register(self.data_socket, zmq.POLLIN)
        poller.register(self.ttl_socket, zmq.POLLIN)
        poller.register(self.command_socket, zmq.POLLIN)

        while not self.exit_event.is_set():
            items = dict(poller.poll(TIMEOUT))

            # Handle arcord data replication
            if self.data_socket in items:
                try:
                    self.handler.OnFrameReceived(Frame.recv(self.data_socket))              
                except:
                    log.info("error")
            # Handle live link heartbeat
            if self.ttl_socket in items:
                request = self.ttl_socket.recv_multipart()
                identity = request[0]

                if self.client_addr is None:
                    self.client_addr = request[2].decode()
                
                self.ttl_socket.send(identity, zmq.SNDMORE)
                self.ttl_socket.send_multipart([b"pong"])
            
            # Handle remote command
            if self.command_socket in items:
                command = self.command_socket.recv_multipart()
                identity = command[0]

                if command[1] == b"SCENE":
                    log.debug("Try to get scene")
                    scene_data_chunk = self.handler.OnGetScene(int(command[2]),int(command[3]))
                   
                    if scene_data_chunk:                        
                        self.command_socket.send(identity, zmq.SNDMORE)
                        self.command_socket.send_multipart([b"SCENE",scene_data_chunk])
                       
                    else:
                        log.info("GetScene not implemented")

                elif command[1] == b"RECORD":
                    result = self.handler.OnRecord(command[2].decode())
                    response = [b"RECORD"]
                    if result:
                        response.append(result.encode())
                    else:
                        response.append(b"STOPPED")

                    self.command_socket.send(identity, zmq.SNDMORE)
                    self.command_socket.send_multipart(response)
                else:
                    log.error("Wrong request")



        log.debug("Exiting App link")

        self.data_socket.close()
        self.ttl_socket.close()
        self.command_socket.close()

    def stop(self):
        self.exit_event.set()




if __name__ == "__main__":
    ar_handler = ArEventHandler()

    def test(frame):
        log.debug(frame.camera.translation)

    ar_handler.bindOnFrameReceived(test)

    ar = ArCoreInterface(ar_handler)

    ar.start()
    time.sleep(5)


    ar.stop()

