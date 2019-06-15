import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
    EnumProperty,
    WindowManager
)
import bpy.utils.previews

import os

class USERPREF_PT_input_devices_smartphone(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "SMARTPHONE_SETTINGS_PT_panel"
    bl_label = "Connexion"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remote"

    def draw(self, context):
        layout = self.layout

        prefs = context.preferences

        # This tells Blender to draw the my_previews window manager object
        # (Which is our preview)
        row = layout.row()
        row.template_icon_view(context.scene, "my_thumbnails")
        row = layout.row()
        row.label(text = bpy.context.preferences.inputs.srLocalIp[1]['default'])
        # if bpy.context.preferences.inputs.srDaemonRunning[1]['default'] == False:
        #     sub.operator("scene.restart_blender_remote")
        # else:
        #     sub.operator("scene.stop_blender_remote")




preview_collections = {}


def generate_previews():
    pcoll = preview_collections["thumbnail_previews"]
    image_location = pcoll.images_location
    VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')

    enum_items = []
    
    # Generate the thumbnails
    for i, image in enumerate(os.listdir(image_location)):
        if image.endswith(VALID_EXTENSIONS):
            filepath = os.path.join(image_location, image)
            thumb = pcoll.load(filepath, filepath, 'IMAGE')
            enum_items.append((image, image, "", thumb.icon_id, i))

    return enum_items


def register():
    from bpy.types import Scene
    from bpy.props import StringProperty, EnumProperty

    pcoll = bpy.utils.previews.new()
    pcoll.images_location = os.path.join(os.path.dirname(__file__), "images")
    preview_collections["thumbnail_previews"] = pcoll

    bpy.types.Scene.my_thumbnails = EnumProperty(
        items=generate_previews(),)
    bpy.utils.register_class(USERPREF_PT_input_devices_smartphone)


def unregister():
    from bpy.types import WindowManager
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)

    preview_collections.clear()
    del bpy.types.Scene.my_thumbnails
    bpy.utils.unregister_class(USERPREF_PT_input_devices_smartphone)


