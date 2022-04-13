import preference, arcore, argparse, os

currentFrame = 0

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
    print ('a')

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

if (__name__ == '__main__'):
    ARHandler = arcore.ArEventHandler()
    ARHandler.bindOnFrameReceived(handleARFrameRecieved)
    ARHandler.bindRecord(handleARRecording)
    AR = arcore.ArCoreInterface(ARHandler, port = int(recieverCLIArgs.recieverCLIArgs_bindPort))
    AR.start()