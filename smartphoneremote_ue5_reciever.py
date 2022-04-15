import preference, arcore, argparse, os, sys, requests, time, math
from scipy.spatial.transform import Rotation as scipy_rotation
import numpy as np

currentFrame = 0
movementMultiplier = 1

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
recieverCLIParser.add_argument(
    '--unreal-engine-api-root', '-u',
    required = False,
    type = str,
    dest = 'recieverCLIArgs_unrealEngineAPIRoot',
    help = '(http://a.d.d.r:port) the root point for the unreal engine web control api (default: http://127.0.0.1:30010)'
)
recieverCLIParser.add_argument(
    '--unreal-engine-camera-path', '-c',
    required = False,
    type = str,
    dest = 'recieverCLIArgs_unrealEngineCameraPath',
    help = 'the path for the unreal engine scene\'s camera (default: debug value)'
)
recieverCLIArgs = recieverCLIParser.parse_args()

if (not recieverCLIArgs.recieverCLIArgs_bindPort): recieverCLIArgs.recieverCLIArgs_bindPort = 8096
if (not recieverCLIArgs.recieverCLIArgs_unrealEngineAPIRoot): recieverCLIArgs.recieverCLIArgs_unrealEngineAPIRoot = 'http://127.0.0.1:30010'
if (not recieverCLIArgs.recieverCLIArgs_unrealEngineCameraPath): recieverCLIArgs.recieverCLIArgs_unrealEngineCameraPath = '/Game/StarterContent/Maps/Minimal_Default.Minimal_Default:PersistentLevel.CineCameraActor_0'
recieverCLIArgs.recieverCLIArgs_generateQRCode = False if (str(recieverCLIArgs.recieverCLIArgs_generateQRCode).lower()  != 'yes') else True
if (recieverCLIArgs.recieverCLIArgs_generateQRCode): preference.generate_connexion_qrcode('{}:{}'.format(preference.get_current_ip(), recieverCLIArgs.recieverCLIArgs_bindPort), os.getcwd())

print('CURRENT BOUND ADDRESS: {}:{}'.format(preference.get_current_ip(), recieverCLIArgs.recieverCLIArgs_bindPort))
print('EASY CONNECT QR CODE SAVED TO CURRENT DIRECTORY' if recieverCLIArgs.recieverCLIArgs_generateQRCode else "NO QR CODE GENERATED (USE -H FOR MORE INFO)")

UE5_VIEW_MATRIX = np.matrix([
    [-1, 0, 0, 0],
    [0, 0, 1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1]
])

def handleARFrameRecieved(frame):
    global currentFrame, lastCameraRotations
    try:
        currentFrame += 1
        if (not currentFrame % 3 == 0): return '' # for pacing the requests
        # i dont know. thanks, internet.
        camPose_orig = frame.camera.view_matrix * UE5_VIEW_MATRIX
        camPose = camPose_orig.tolist()
        camOrigin = frame.root.world_matrix * UE5_VIEW_MATRIX
        phi_y = np.arctan2(camPose[0][2], math.sqrt(1 - (camPose[0][2])**2))  #angle beta in wiki
        # or just phi_y = np.arcsin(R[0,2])
        phi_x = np.arctan2(-camPose[1][2],camPose[2][2])    #angle alpha in wiki
        phi_z = np.arctan2(-camPose[0][1],camPose[0][0])    #angle gamma in wiki
        cameraRotation = [math.degrees(phi_x), math.degrees(phi_y), math.degrees(phi_z)]
        camPose[3] = (camPose_orig[3] - camOrigin[3])*(1/np.linalg.norm(camOrigin[1])).tolist()
        cameraLocation = camPose[3].tolist()[-1]

        # send the data
        rotationRequestJSONDataRotation = {
            "objectPath" : recieverCLIArgs.recieverCLIArgs_unrealEngineCameraPath,
            "functionName":"SetActorRotation",
            "parameters": {
                "NewRotation": {
                    "Pitch": 270 - cameraRotation[0],
                    "Yaw": cameraRotation[2],
                    "Roll": 360 - cameraRotation[1]
                }
            },
            "generateTransaction":False
        }
        requests.put(recieverCLIArgs.recieverCLIArgs_unrealEngineAPIRoot + '/remote/object/call', json = rotationRequestJSONDataRotation)
        rotationRequestJSONDataLocation = {
            "objectPath" : recieverCLIArgs.recieverCLIArgs_unrealEngineCameraPath,
            "functionName":"SetActorLocation",
            "parameters": {
                "NewLocation": {
                    "X": math.degrees(cameraLocation[1]) * movementMultiplier,
                    "Y": math.degrees(cameraLocation[0]) * movementMultiplier,
                    "Z": math.degrees(cameraLocation[2]) * movementMultiplier
                }
            },
            "generateTransaction":False
        }
        requests.put(recieverCLIArgs.recieverCLIArgs_unrealEngineAPIRoot + '/remote/object/call', json = rotationRequestJSONDataLocation)
    except Exception as ex:
        print(ex)
        # -------------- DEBUG --------------
        trace = []
        tb = ex.__traceback__
        while tb is not None:
            trace.append({
                "filename": tb.tb_frame.f_code.co_filename,
                "name": tb.tb_frame.f_code.co_name,
                "lineno": tb.tb_lineno
            })
            tb = tb.tb_next
        print(str({
            'type': type(ex).__name__,
            'message': str(ex),
            'trace': trace
        }))
        # -------------- DEBUG --------------

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
        exit()
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