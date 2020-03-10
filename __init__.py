bl_info = {
    "name": "Blender remote",
    "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "Allow to use smartphone as a controller",
    "category": "System",
    "support": "COMMUNITY",
    "tracker_url": "https://gitlab.com/slumber/smartphoneremote/-/issues",
    "wiki_url": "https://gitlab.com/slumber/smartphoneremote/-/wikis/Quick-start",
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


def register():
    environment.setup(DEPENDENCIES)
    
    from . import settings, operators, preference
    
    preference.register()

    app_address = preference.get_current_ip()
    
    bpy.types.PreferencesInput.srLocalIp = bpy.props.StringProperty(
        name="Interface address", default=app_address)
    bpy.types.PreferencesInput.srDaemonRunning = bpy.props.BoolProperty(
        name="Daemon running", default=True)

    settings.register()
    operators.register()


def unregister():
    environment.clean()

    from . import settings, operators, preference

    settings.unregister()
    operators.unregister()
    preference.unregister()


if __name__ == "__main__":
    register()
