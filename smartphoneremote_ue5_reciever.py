import preference, arcore, argparse, os, sys, requests, time
from scipy.spatial.transform import Rotation as scipy_rotation
import numpy as np

currentFrame = 0

# make these two vars into cli args
UE5RemoteControlServerEndpointAddress = 'http://127.0.0.1:30010'
UE5CameraObjectPath = '/Game/StarterContent/Maps/Minimal_Default.Minimal_Default:PersistentLevel.CineCameraActor_0'

recieverCLIParser = argparse.ArgumentParser(description = 'Smartphone Remote middleman for UE5.')
recieverCLIParser.add_argument(
    '--bind', '-b', 
    required = False,
    type = int, 
    dest = 'recieverCLIArgs_bindPort',
    help = 'the port where the reciever will listen for incoming connections (always listens on 0.0.0.0) (default: 8096)',
)
recieverCLIParser.add_argument(
    '--generate-qr-code', '-g',
    required = False,
    type = str,
    dest = 'recieverCLIArgs_generateQRCode',
    help = '(yes/no) whether or not the program should generate a QR code for easy connections (default: no)'
)
recieverCLIArgs = recieverCLIParser.parse_args()

if (not recieverCLIArgs.recieverCLIArgs_bindPort): recieverCLIArgs.recieverCLIArgs_bindPort = 8096
recieverCLIArgs.recieverCLIArgs_generateQRCode = False if (str(recieverCLIArgs.recieverCLIArgs_generateQRCode).lower()  != 'yes') else True

if (recieverCLIArgs.recieverCLIArgs_generateQRCode): preference.generate_connexion_qrcode('{}:{}'.format(preference.get_current_ip(), recieverCLIArgs.recieverCLIArgs_bindPort), os.getcwd())

print('CURRENT BOUND ADDRESS: {}:{}'.format(preference.get_current_ip(), recieverCLIArgs.recieverCLIArgs_bindPort))
print('EASY CONNECT QR CODE SAVED TO CURRENT DIRECTORY' if recieverCLIArgs.recieverCLIArgs_generateQRCode else "NO QR CODE GENERATED (USE -H FOR MORE INFO)")

def handleARFrameRecieved(frame):
    global currentFrame
    currentFrame += 1 # comes first in case a frame is dropped
    cameraRotation = scipy_rotation.from_quat(frame.camera.view_matrix)
    cameraRotation = cameraRotation.as_euler('xyz', degrees = True).tolist()
    rotationRequestJSONData = {
        "objectPath" : UE5CameraObjectPath,
        "functionName":"SetActorRotation",
        "parameters": {
            "NewRotation": {
                "Pitch":cameraRotation[0],
                "Yaw":cameraRotation[2],
                "Roll":cameraRotation[1]
            }
        },
        "generateTransaction":False
    }
    requests.put(UE5RemoteControlServerEndpointAddress + '/remote/object/call', json = rotationRequestJSONData)

def handleARRecording(status):
    global currentFrame
    returnState = 'NONE'
    if (status == 'START'): # start
        returnState = 'STARTED'
        print('STARTED RECORDING')
    elif (status == 'STATE'): # update
        returnState = str(currentFrame)
    elif (status == 'STOP'): # stop
        returnState = 'STOPPED'
        print('STOPPED RECORDING')
    return returnState

def handleARGetScene(*args):
    return b''

if (__name__ == '__main__'):
    ARHandler = arcore.ArEventHandler()
    ARHandler.bindOnFrameReceived(handleARFrameRecieved)
    ARHandler.bindRecord(handleARRecording)
    ARHandler.bindGetScene(handleARGetScene)
    AR = arcore.ArCoreInterface(ARHandler, port = int(recieverCLIArgs.recieverCLIArgs_bindPort))
    AR.start()