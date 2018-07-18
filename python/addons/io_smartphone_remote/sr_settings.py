import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
    EnumProperty,
    WindowManager,
)
import bpy.utils.previews

import os


class SmartphoneRemoteSettingsPanel(Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Smartphone"
    bl_idname = "PREF_Smratphone_Remote"
    bl_space_type = 'USER_PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "Input"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'INPUT')

    @staticmethod
    def draw(self, layout):

        layout = self.layout
        wm = context.window_manager
        row = layout.row()
        # This tells Blender to draw the my_previews window manager object
        # (Which is our preview)
        row.template_icon_view(context.scene, "my_thumbnails")

        # Just a way to access which one is selected
        row = layout.row()
        row.label(text="You selected: " + bpy.context.scene.my_thumbnails)


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
    bpy.utils.register_class(SmartphoneRemoteSettingsPanel)


def unregister():
    from bpy.types import WindowManager
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    del bpy.types.Scene.my_thumbnails

    bpy.utils.unregister_class(SmartphoneRemoteSettingsPanel)


if __name__ == "__main__":
    register()
