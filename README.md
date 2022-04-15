# Smartphone Remote UE5

*A Python middleman for the Smartphone Remote app, and Unreal Engine 5. This enables remote control of the camera in UE5 using a smartphone.*

https://user-images.githubusercontent.com/38505228/163592853-01ae9b15-cdca-4625-95c9-ff90358eef64.mp4

*(Yaw, roll, pitch, and location can be transferred from an Android phone to UE5 via this script.)*

## Original Repos:

- https://gitlab.com/slumber/smartphoneremote

- https://gitlab.com/slumber/smartphoneremoteandroid

## Setup Instructions:

1.] `git clone https://github.com/katznboyz1/smartphoneremote_ue5 %% cd smartphoneremote_ue5`

2.] `python3 -m pip install -r requirements.txt`

3.] Download the smartphone remote APK from this repo's releases. Downloading it from anywhere else is at your own risk.

## CLI Args:

`--bind` / `-b` : The port where the program will listen for incoming connections from the smartphone app. [Not required, default is 8096].

`--generate-qr-code` / `-g` : Whether or not the program should generate a QR code that you can scan with your phone to connect to the middleman. [Not required, default is no].

`--unreal-engine-api-root` / `-u` : The root point for the Unreal Engine web control API. [Not required, default is http://127.0.0.1:30010].

`--unreal-engine-camera-path` / `-c` : The path for the camera in Unreal Engine. [Not required, however this will likely not work if you don't set it manually, as the default is specific to my debug environment].

`--camera-z-rotation-offset` / `-z` : The Z rotation [yaw] offset for the camera. This is additive. [Not required, default is 0].

`--speed-dividend` / `-s` : Only send a PUT request to the Unreal Engine API every N'th frame. [Not required, default is 2].

## Running the Program

1.] Start Unreal Engine with the web control plugin enabled and configured.

2.] `python3 smartphoneremote_ue5_reciever.py [args]`

3.] Scan the QR code/enter the information on your phone to connect to the middleman.
