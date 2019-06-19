import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
    EnumProperty,
    WindowManager
)
import bpy.utils.previews
from . import environment, operators

import os

class USERPREF_PT_input_devices_smartphone(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "SMARTPHONE_SETTINGS_PT_panel"
    bl_label = "General"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remote"

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences

        
        
        row = layout.row()
        if operators.app and operators.app.is_running():
            row = layout.row()
            row.template_icon_view(context.scene, "qrcodes")
            row = layout.row()
            status_box = row.box()
            detail_status_box = status_box.row()
            detail_status_box.label(text=prefs.inputs.srLocalIp[1]['default'])
            row = layout.row()
            row.operator("remote.stop",text="STOP")
            
            

        else:
            row.operator("remote.start",text="START")


class USERLIST_PT_input_devices_smartphone(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "SMARTPHONE_SETTINGS_PT_panel"
    bl_label = "clients"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remote"

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences

        # TODO: List connected remotes


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


def register():
    from bpy.types import Scene
    from bpy.props import StringProperty, EnumProperty

    pcoll = bpy.utils.previews.new()
    pcoll.images_location = os.path.join(os.path.dirname(__file__), "cache")
    preview_collections["thumbnail_previews"] = pcoll

    bpy.types.Scene.qrcodes = EnumProperty(
        items=generate_previews(),)
    bpy.utils.register_class(USERPREF_PT_input_devices_smartphone)


def unregister():
    from bpy.types import WindowManager
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)

    preview_collections.clear()
    del bpy.types.Scene.qrcodes
    bpy.utils.unregister_class(USERPREF_PT_input_devices_smartphone)


