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
import bpy
import os
import socket

from . import environment, operators

logger = logging.getLogger(__name__)

preview_collections = {}


def generate_previews():
    pcoll = preview_collections["thumbnail_previews"]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []
    
    # Generate the thumbnails
    for i, image in enumerate(os.listdir(environment.CACHE_DIR)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))

    return enum_items
    
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

def update_qr_code(self, dummy):
    app_address = get_current_ip()
    prefs = get()
    generate_connexion_qrcode(f"{app_address}:{prefs.port}")

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
        
    pcoll = bpy.utils.previews.new()
    pcoll.images_location = os.path.join(os.path.dirname(__file__), "cache")
    preview_collections["thumbnail_previews"] = pcoll

    bpy.types.Scene.qrcodes = bpy.props.EnumProperty(
        items=generate_previews(),)
    
class SmartphoneRemotePrefs(bpy.types.AddonPreferences):
    bl_idname  = __package__
    
    port: bpy.props.IntProperty(
        name="port",
        description='Smartphone remote service port',
        default=61520,
        update=update_qr_code,
        )

    cache_directory: bpy.props.StringProperty(
        name="cache directory",
        subtype="DIR_PATH",
        default=environment.CACHE_DIR)

    category: bpy.props.EnumProperty(
        name="Category",
        description="Preferences Category",
        items=[
            ('CONFIG', "Configuration", "Configuration about this add-on"),
            ('UPDATE', "Update", "Update this add-on"),
        ],
        default='CONFIG'
    )

    auto_check_update: bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )
    updater_intrval_months: bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days: bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31
    )
    updater_intrval_hours: bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        layout = self.layout

        layout.row().prop(self, "category", expand=True)
        
        if self.category == 'CONFIG':
            row = layout.row()
            row.prop(self, 'cache_directory')

            row = layout.row()
            row.label(text='port :')
            row.prop(self, 'port', text="")

        if self.category == 'UPDATE':
            from . import addon_updater_ops
            addon_updater_ops.update_settings_ui_condensed(self, context)

classes = (
    SmartphoneRemotePrefs,
)

def get():
    return bpy.context.preferences.addons[__package__].preferences

def register():
    from bpy.utils import register_class
    

    for cls in classes:
        register_class(cls)
    
    prefs = bpy.context.preferences.addons[__package__].preferences

    update_qr_code(None,None)

    

def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)