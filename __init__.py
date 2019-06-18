bl_info = {
    "name": "Blender remote",
    "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "Allow to use smartphone as a controller",
    "category": "System",
}


import addon_utils
import random
import string
import subprocess
import sys
import os
import bpy

from . import environment 

DEPENDENCIES = {
    "zmq",
    "umsgpack",
}


def generate_connexion_qrcode(app_address):
    import pyqrcode

    url = pyqrcode.create(app_address)

    if not os.path.exists(environment.CACHE_DIR):
        os.makedirs(environment.CACHE_DIR)

    url.png(os.path.join(environment.CACHE_DIR ,environment.QR_FILE),  scale=4)
    

def register():
    environment.setup(DEPENDENCIES)
    
    from . import settings, operators
    
    app_address = operators.GetCurrentIp()

    generate_connexion_qrcode(app_address)
    
    bpy.types.PreferencesInput.srLocalIp = bpy.props.StringProperty(
        name="Interface address", default=app_address)
    bpy.types.PreferencesInput.srDaemonRunning = bpy.props.BoolProperty(
        name="Daemon running", default=True)
    
    settings.register()
    operators.register()


def unregister():
    environment.clean()

    from . import settings, operators
    # operators.stop_daemons()
    settings.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
