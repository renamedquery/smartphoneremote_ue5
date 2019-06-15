bl_info = {
    "name": "Blender remote",
    "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "description": "Allow to use smartphone as a controller",
    "category": "System",
}

from pathlib import Path
import addon_utils
import random
import string
import subprocess
import sys
import os
import bpy

DEPENDENCIES = {
    "zmq",
    "umsgpack",
}

thirdPartyDir = os.path.dirname(os.path.abspath(__file__))+"/libs"
def module_can_be_imported(name):
    try:
        __import__(name)
        return True
    except ModuleNotFoundError:
        return False

def get_package_install_directory():
    for path in sys.path:
        if os.path.basename(path) in ("dist-packages", "site-packages"):
            return path

python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent
target = get_package_install_directory()

def install_pip():
    # pip can not necessarily be imported into Blender after this
    get_pip_path = Path(__file__).parent / "libs" / "get-pip.py"
    subprocess.run([str(python_path), str(get_pip_path)], cwd=cwd_for_subprocesses)


def install_package(name):
    target = get_package_install_directory()
    
    subprocess.run([str(python_path), "-m", "pip", "install",
                        name, '--target', target], cwd=cwd_for_subprocesses)
def generate_connexion_qrcode(app_address):
    import pyqrcode

    url = pyqrcode.create(app_address)
    url.png(os.path.dirname(os.path.abspath(__file__)) +
            "\\images\\connect.png",  scale=4)
    

def register():
    if thirdPartyDir in sys.path:
        print('Third party module already added')
    else:
        print('Adding local modules dir to the path')
        sys.path.insert(0, thirdPartyDir)

    if not module_can_be_imported("pip"):
        install_pip()
        

    for dep in DEPENDENCIES:
        if not module_can_be_imported(dep):
            install_package(dep)
    
    from . import settings, operators

    app_address = operators.GetCurrentIp()

    generate_connexion_qrcode(app_address)
    
    bpy.types.PreferencesInput.srLocalIp = bpy.props.StringProperty(
        name="Interface address", default=app_address)
    bpy.types.PreferencesInput.srDaemonRunning = bpy.props.BoolProperty(
        name="Daemon running", default=True)
    

    settings.register()
    operators.register()
    # operators.Launch()
    # operators.register()
    # atexit.register(operators.kill_daemons)


def unregister():
    if thirdPartyDir in sys.path:
        print('Cleanup the path')
        sys.path.remove(thirdPartyDir)
    else:
        print('Nothing to clean')

    from . import settings, operators
    # operators.stop_daemons()
    settings.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
