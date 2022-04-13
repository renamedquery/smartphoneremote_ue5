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


import logging
import os
import socket

logger = logging.getLogger(__name__)

preview_collections = {}
    
def get_current_ip():
    """
    Retrieve the main network interface IP.

    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def generate_connexion_qrcode(app_address):
    import pyqrcode

    logger.info('Generating connexion qrcode (addr: {}) '.format(app_address))
    url = pyqrcode.create(app_address)
    prefs = get()
    if not os.path.exists(prefs.cache_directory):
        os.makedirs(prefs.cache_directory)

    qr_path = os.path.join(prefs.cache_directory ,environment.QR_FILE)

    url.png(qr_path,  scale=4)
    logger.info('Success, qrcode saved in {}.'.format(qr_path))