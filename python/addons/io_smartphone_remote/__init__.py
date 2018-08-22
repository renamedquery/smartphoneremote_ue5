bl_info = {
    "name": "Blender remote",
    "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
    "version": (1, 0),
    "blender": (2, 81, 0),
    "location": "View3D",
    "description": "Allow to use smartphone as a controller",
    "category": "System",
}

import bpy
import sys
import os

thirdPartyDir = os.path.dirname(os.path.abspath(__file__))+"/libs"

def register():
    if thirdPartyDir in sys.path:
        print('Third party module already added')
    else:
        print('Adding local modules dir to the path')
        sys.path.insert(0, thirdPartyDir)

    from . import sr_settings,sr_daemon
    import pyqrcode


    app = sr_daemon.GetCurrentIp()+":8080"
    bpy.types.UserPreferencesInput.srLocalIp = bpy.props.StringProperty(name = "Interface address", default=app)
    bpy.types.UserPreferencesInput.srDaemonRunning = bpy.props.BoolProperty(name = "Daemon running", default=True)
    url = pyqrcode.create(app)
    url.png(os.path.dirname(os.path.abspath(__file__))+"/images/connect.png",  scale=4)

    sr_settings.register()
    # sr_daemon.Launch()
    sr_daemon.register()

def unregister():
    if thirdPartyDir in sys.path:
        print('Cleanup the path')
        sys.path.remove(thirdPartyDir)
    else:
        print('Nothing to clean')

    from . import (sr_settings,sr_daemon)
    import async_loop

    async_loop.unregister();
    sr_settings.unregister()




if __name__ == "__main__":
    register()
