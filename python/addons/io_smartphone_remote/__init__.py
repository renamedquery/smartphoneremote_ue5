bl_info = {
    "name": "Blender remote",
    "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
    "version": (1, 0),
    "blender": (2, 8, 0),
    "location": "View3D",
    "description": "Allow to use smartphone as a controller",
    "category": "System",
}

import bpy
from . import sr_settings
from io_smartphone_remote.libs import pyqrcode



def register():
    print('hi')
    qr = pyqrcode.create('Unladden swallow')
    qr.png('famous-joke.png', scale=5)
    # sr_settings.register()
    # bpy.utils.register_class(SettingsPanel)
    # bpy.utils.register_module(__name__)
    pass
    # import sys
    #
    # # Support reloading
    # if '%s.blender' % __name__ in sys.modules:
    #     import importlib
    #
    #     def reload_mod(name):
    #         modname = '%s.%s' % (__name__, name)
    #         try:
    #             old_module = sys.modules[modname]
    #         except KeyError:
    #             # Wasn't loaded before -- can happen after an upgrade.
    #             new_module = importlib.import_module(modname)
    #         else:
    #             new_module = importlib.reload(old_module)
    #
    #         sys.modules[modname] = new_module
    #         return new_module
    #
    #     async_loop = reload_mod('async_loop')
    # else:
    #     from . import (async_loop,)
    #
    # async_loop.setup_asyncio_executor()
    # async_loop.register()


def unregister():
    # sr_settings.unregister()
    # bpy.utils.unregister_class(SettingsPanel)
    # bpy.utils.unregister_module(__name__)
    pass
    # from . import (async_loop)
    # async_loop.unregister()


if __name__ == "__main__":
    register()
