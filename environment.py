import sys
import os
from pathlib import Path
import bpy

CACHE_DIR = "cache"
QR_FILE  = "connexion.png"
SCENE_FILE = "scene_cache.glb"

thirdPartyDir = os.path.dirname(os.path.abspath(__file__))+"/libs"
python_path = Path(bpy.app.binary_path_python)
cwd_for_subprocesses = python_path.parent
target = None

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


def install_pip():
    # pip can not necessarily be imported into Blender after this
    get_pip_path = Path(__file__).parent / "libs" / "get-pip.py"
    subprocess.run([str(python_path), str(get_pip_path)], cwd=cwd_for_subprocesses)


def install_package(name):
    target = get_package_install_directory()
    
    subprocess.run([str(python_path), "-m", "pip", "install",
                        name, '--target', target], cwd=cwd_for_subprocesses)

def setup(dependencies):
    if not module_can_be_imported("pip"):
        install_pip()

    setup_python_path()

    for dep in dependencies:
        if not module_can_be_imported(dep):
            install_package(dep)

def setup_python_path():

    if thirdPartyDir in sys.path:
        print('Third party module already added')
    else:
        print('Adding local modules dir to the path')
        sys.path.insert(0, thirdPartyDir)

def clean():
    clean_python_path()
    
def clean_python_path():
    if thirdPartyDir in sys.path:
        print('Cleanup the path')
        sys.path.remove(thirdPartyDir)
    else:
        print('Nothing to clean')