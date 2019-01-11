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
    bl_label = "Smartphone"
    bl_idname = "USERPREF_PT_input_devices"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences

        row = layout.row()
        col = row.column()
        sub = col.column()
        sub.label(text="Smartphone:")
        # This tells Blender to draw the my_previews window manager object
        # (Which is our preview)
        sub.template_icon_view(context.scene, "my_thumbnails")
        sub.label(text = bpy.context.preferences.inputs.srLocalIp[1]['default'])
        if bpy.context.preferences.inputs.srDaemonRunning[1]['default'] == False:
            sub.operator("scene.restart_blender_remote")
        else:
            sub.operator("scene.stop_blender_remote")

        #UGLY
        sub = row.column()
        sub.label(text="   ")
        sub = row.column()
        sub.label(text="   ")
        sub = row.column()
        sub.label(text="   ")



preview_collections = {}


def generate_previews():
    # We are accessing all of the information that we generated in the register function below
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

    # Create a new preview collection (only upon register)
    pcoll = bpy.utils.previews.new()

    # This line needs to be uncommented if you install as an addon
    pcoll.images_location = os.path.join(os.path.dirname(__file__), "images")

    # This line is for running as a script. Make sure images are in a folder called images in the same
    # location as the Blender file. Comment out if you install as an addon
    # pcoll.images_location = bpy.path.abspath('//images')

    # Enable access to our preview collection outside of this function
    preview_collections["thumbnail_previews"] = pcoll

    # This is an EnumProperty to hold all of the images
    # You really can save it anywhere in bpy.types.*  Just make sure the location makes sense
    bpy.types.Scene.my_thumbnails = EnumProperty(
        items=generate_previews(),)
    bpy.utils.register_class(USERPREF_PT_input_devices_smartphone)


def unregister():
    from bpy.types import WindowManager
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
        # bpy.utils.previews.remove()
    preview_collections.clear()

    del bpy.types.Scene.my_thumbnails

    bpy.utils.unregister_class(USERPREF_PT_input_devices_smartphone)


if __name__ == "__main__":
    register()
