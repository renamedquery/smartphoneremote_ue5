import zmq
import umsgpack
import numpy as np

import threading
import logging
import time

TIMEOUT = 1

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Camera():
    def __init__(self, translation = [0,0,0], rotation=[0,0,0,0],vm= None):
        self.rotation= rotation
        self.translation = translation
        if vm:
            self.view_matrix =  np.matrix([[vm[0],vm[1],vm[2],vm[3]],
                                        [vm[4],vm[5],vm[6],vm[7]],
                                        [vm[8],vm[9],vm[10],vm[11]],
                                        [vm[12],vm[13],vm[14],vm[15]]])
        else:
            self.view_matrix = np.matrix(np.zeros((4, 4)))

class Node():
    def __init__(self, translation = [0,0,0], rotation=[0,0,0,0],scale = [1,1,1], wm = None):
        self.rotation= rotation
        self.translation = translation
        self.scale = scale

        if wm:
            self.world_matrix =  np.matrix([[wm[0],wm[1],wm[2],wm[3]],
                                        [wm[4],wm[5],wm[6],wm[7]],
                                        [wm[8],wm[9],wm[10],wm[11]],
                                        [wm[12],wm[13],wm[14],wm[15]]])
        else:
            self.world_matrix = np.matrix(np.zeros((4, 4)))


class Frame():
    def __init__(self, camera = Camera(),root = Node()):
        self.camera = camera
        self.root = root


class ArEventHandler():
    def __init__(self):
        self._frameListeners = []
        self._getScene = None
    
    def bindOnFrameReceived(self,f):
        self._frameListeners.append(f)
    
    def bindGetScene(self, f):
        self._getScene = f

    def OnFrameReceived(self, frame):
        for f in self._frameListeners:
            f(frame)
    
    def GetScene(self):
        if self._getScene:
            return self._getScene()
        else:
            return None


class ArCoreInterface(object):
    def __init__(self, handler):
        self._net_link = AppLink(handler)
        self.handler = handler

    def start(self):
        self._net_link.start()
  
    def is_running(self):
        return self._net_link.is_alive()

    def stop(self):
        self._net_link.stop()


class AppLink(threading.Thread):
    def __init__(self, handler, context=zmq.Context.instance(), name="Applink"):
        threading.Thread.__init__(self)
        self.name = name
        self.daemon = True
        self.status = 0  # 0: idle, 1: Connecting, 2: Connected\

        self.context = context
        self.command_socket = self.context.socket(zmq.REP)
        self.command_socket.bind("tcp://*:5559")
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.bind("tcp://*:5558")
        self.ttl_socket = self.context.socket(zmq.REP)
        self.ttl_socket.bind("tcp://*:5557")
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
            
            if self.data_socket in items:
                frame_buffer = self.data_socket.recv_multipart()
                frame = Frame()

                while len(frame_buffer)>0:
                    header =  frame_buffer.pop(0)
                    if header == b"CAMERA":
                        arCamera = Camera(
                            rotation=umsgpack.unpackb(frame_buffer.pop(0)),
                            translation=umsgpack.unpackb(frame_buffer.pop(0)),
                            vm=umsgpack.unpackb(frame_buffer.pop(0))
                            )
                        frame.camera = arCamera        
                    if header == b"NODE":
                        arNode = Node(
                            rotation=umsgpack.unpackb(frame_buffer.pop(0)),
                            translation=umsgpack.unpackb(frame_buffer.pop(0)),
                            scale=umsgpack.unpackb(frame_buffer.pop(0)),
                            wm=umsgpack.unpackb(frame_buffer.pop(0))
                            )
                        frame.root = arNode

                self.handler.OnFrameReceived(frame)

            if self.ttl_socket in items:
                request = self.ttl_socket.recv()

                if self.client_addr is None:
                    self.client_addr = request.decode()
                    # self.push_socket.connect("tcp://{}:5559".format(self.client_addr))
                    self.ttl_socket.send_string("pong")
                else:
                    log.info(request.decode())
                    frame = [b"SCENE",b"TOTOT"]
                    self.ttl_socket.send_multipart(frame)
                # if self.client_addr and self.client_addr != request.decode():
            
            if self.command_socket in items:
                command = self.command_socket.recv()

                if command == b"SCENE":
                    scene_data = self.handler.GetScene()

                    if scene_data:
                        self.command_socket.send(scene_data)
                    else:
                        log.info("GetScene not implemented")

                    log.info("request scene")
                else:
                    log.info("request peon")
                
                

        log.debug("Exiting App link")
        self.data_socket.close()
        self.ttl_socket.close()
        self.command_socket.close()
        self.exit_event.clear()

    def stop(self):
        self.exit_event.set()
        
        #Wait the end of the run
        while self.exit_event.is_set():
            time.sleep(.1)


if __name__ == "__main__":
    ar_handler = ArEventHandler()

    def test(frame):
        log.debug(frame.camera.translation)
    
    ar_handler.append(test)
    
    ar = ArCoreInterface(ar_handler)

    ar.start()
    time.sleep(5)


    ar.stop()

