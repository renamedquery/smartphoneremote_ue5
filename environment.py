# ##### BEGIN GPL LICENSE BLOCK #####
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import sys
import os
from pathlib import Path
import bpy
import logging
import subprocess


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CACHE_DIR = os.path.dirname(os.path.abspath(__file__))+"/cache"
QR_FILE  = "connexion.png"
SCENE_FILE = "scene_cache.glb"
PORT = 5560


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
    log.info('Installing module: {}'.format(name))
    
    subprocess.run([str(python_path), "-m", "pip", "install",
                        name], cwd=cwd_for_subprocesses)
    log.info('{} module successfully installed.'.format(name))

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