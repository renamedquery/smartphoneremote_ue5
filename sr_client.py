import zmq
import umsgpack

import threading
import logging
import time

logging.basicConfig(level=logging.DEBUG)


class Camera():
    def __init__(self, translation = [0,0,0], rotation=[0,0,0,0]):
        self.rotation= rotation
        self.translation = translation
class Frame():
    def __init__(self, camera = Camera()):
        self.camera = camera

class ArEventHandler():
    def __init__(self):
        self.bindings = []
    
    def append(self,f):
        self.bindings.append(f)

    def OnFrameReceived(self, frame):
        for f in self.bindings:
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
        self.data_socket.bind("tcp://*:5556")

        self.exit_event = threading.Event()
        self.handler = handler

    def run(self):
        import logging

        logging.debug("Running App link")

        while not self.exit_event.is_set():
            try:
                frame_buffer = self.data_socket.recv_multipart()
                
                if frame_buffer[0] == "CAMERA":
                    frame_cam = Camera(
                        rotation=umsgpack.unpackb(frame_buffer[1]),
                        translation=umsgpack.unpackb(frame_buffer[2])
                        )
                    
                received_frame = Frame(camera=frame_cam)
                
                self.handler.OnFrameReceived(received_frame)
                
            except Exception as e:
                logging.debug(e)

          

        logging.debug("Exiting App link")
        self.exit_event.clear()

    def stop(self):
        self.exit_event.set()
        
        #Wait the end of the run\
        while self.exit_event.is_set():
            time.sleep(.1)



if __name__ == "__main__":
    ar_handler = ArEventHandler()

    def test(frame):
        logging.debug(frame.camera.translation)
    
    ar_handler.append(test)
    
    ar = ArCoreInterface(ar_handler)

    ar.start()
    time.sleep(100)


    # ar.stop()

