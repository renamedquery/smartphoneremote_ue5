import preference, arcore, argparse, os, sys, requests, time
from scipy.spatial.transform import Rotation as scipy_rotation
import numpy as np

currentFrame = 0
lastCameraRotationsToCapture = 24
lastCameraRotations = [[], [], []]

for rotationFiller in range(lastCameraRotationsToCapture):
    lastCameraRotations[0].append(0)
    lastCameraRotations[1].append(0)
    lastCameraRotations[2].append(0)

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
    help = '(http://a.d.d.r:port) the root point for the unrean engine web control api (default: http://127.0.0.1:30010)'
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

# https://automaticaddison.com/how-to-convert-a-quaternion-into-euler-angles-in-python/
def euler_from_quaternion(x, y, z, w):
    """
    Convert a quaternion into euler angles (roll, pitch, yaw)
    roll is rotation around x in radians (counterclockwise)
    pitch is rotation around y in radians (counterclockwise)
    yaw is rotation around z in radians (counterclockwise)
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)
    
    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)
    
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)
    
    return roll_x, pitch_y, yaw_z # in radians

def handleARFrameRecieved(frame):
    global currentFrame, lastCameraRotations
    try:
        #print(frame.camera.view_matrix)
        #cameraRotation = euler_from_quaternion(*frame.camera.view_matrix)
        #for axis in range(3):
        #    lastCameraRotations[axis].append(cameraRotation[axis])
        #    cameraRotation = sum(lastCameraRotations[axis]) / len(lastCameraRotations[axis])
        cameraRotation = scipy_rotation.from_quat(frame.camera.view_matrix)
        cameraRotation = cameraRotation.as_euler('xyz', degrees = True).tolist()
        rotationRequestJSONData = {
            "objectPath" : recieverCLIArgs.recieverCLIArgs_unrealEngineCameraPath,
            "functionName":"SetActorRotation",
            "parameters": {
                "NewRotation": {
                    "Pitch":0, #cameraRotation[0],
                    "Yaw":cameraRotation[2],
                    "Roll":0, #cameraRotation[1]
                }
            },
            "generateTransaction":False
        }
        requests.put(recieverCLIArgs.recieverCLIArgs_unrealEngineAPIRoot + '/remote/object/call', json = rotationRequestJSONData)
        currentFrame += 1
    except Exception as ex:
        print(ex)
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