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