import zmq
import umsgpack

import threading
import logging
import time

TIMEOUT = 1

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class Camera():
    def __init__(self, translation = [0,0,0], rotation=[0,0,0,0]):
        self.rotation= rotation
        self.translation = translation


class Frame():
    def __init__(self, camera = Camera()):
        self.camera = camera


class ArEventHandler():
    def __init__(self):
        self.listeners = []
    
    def append(self,f):
        self.listeners.append(f)

    def OnFrameReceived(self, frame):
        for f in self.listeners:
            f(frame)


class ArCoreInterface(object):
    def __init__(self, handler):
        self._net_link = AppLink(handler)
        self.handler = handler 
    def start(self):
        self._net_link.start()

    def stop(self):
        self._net_link.stop()


class AppLink(threading.Thread):
    def __init__(self, handler, context=zmq.Context.instance(), name="Applink"):
        threading.Thread.__init__(self)
        self.name = name
        self.daemon = True
        self.status = 0  # 0: idle, 1: Connecting, 2: Connected\

        self.context = context
        self.data_socket = self.context.socket(zmq.PULL)
        self.data_socket.bind("tcp://*:5558")
        self.ttl_socket = self.context.socket(zmq.REP)
        self.ttl_socket.bind("tcp://*:5557")

        self.exit_event = threading.Event()
        self.handler = handler

    def run(self):
        log.debug("Running App link")

        poller = zmq.Poller()
        poller.register(self.data_socket, zmq.POLLIN)
        poller.register(self.ttl_socket, zmq.POLLIN)
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
                            translation=umsgpack.unpackb(frame_buffer.pop(0))
                            )
                        frame.camera = arCamera        
                
                    self.handler.OnFrameReceived(frame)

            if self.ttl_socket in items:
                request = self.ttl_socket.recv()
                self.ttl_socket.send_string("pong")

        log.debug("Exiting App link")
        self.data_socket.close()
        self.ttl_socket.close()
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

