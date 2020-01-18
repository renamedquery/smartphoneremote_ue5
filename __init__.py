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
import sys
import os
import bpy
import logging

from . import environment 

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DEPENDENCIES = {
    "zmq",
    "umsgpack",
}


def generate_connexion_qrcode(app_address):
    import pyqrcode

    log.info('Generating connexion qrcode (addr: {}) '.format(app_address))
    url = pyqrcode.create(app_address)

    if not os.path.exists(environment.CACHE_DIR):
        os.makedirs(environment.CACHE_DIR)

    qr_path = os.path.join(environment.CACHE_DIR ,environment.QR_FILE)

    url.png(qr_path,  scale=4)
    log.info('Success, qrcode saved in {}.'.format(qr_path))
    

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

    settings.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
