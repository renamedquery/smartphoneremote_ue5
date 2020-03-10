import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
    EnumProperty,
    WindowManager
)
import bpy.utils.previews
from . import environment, operators, preference

import os

class SMARTPHONEREMOTE_PT_settings(Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "SMARTPHONE_SETTINGS_PT_panel"
    bl_label = "General"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Remote"

    def draw(self, context):
        layout = self.layout

        prefs = preference.get()
       
        row = layout.row()
        if operators.app and operators.app.is_running():
            ip = context.preferences.inputs.srLocalIp[1]['default']
            port = prefs.port

            row = layout.row()
            row.template_icon_view(context.scene, "qrcodes")
            row = layout.row()
            status_box = row.box()
            detail_status_box = status_box.row()
            detail_status_box.label(text=f"{ip}:{port}")
            row = layout.row()
            row.operator("remote.stop",text="STOP")
        else:
            row.label(text="Service port:")
            row.prop(prefs, 'port', text="")
            row = layout.row()
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


def register():
    
    bpy.utils.register_class(SMARTPHONEREMOTE_PT_settings)


def unregister():
    from bpy.types import WindowManager
    

    del bpy.types.Scene.qrcodes
    bpy.utils.unregister_class(SMARTPHONEREMOTE_PT_settings)


