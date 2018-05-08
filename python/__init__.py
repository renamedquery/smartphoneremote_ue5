bl_info = {
 "name": "Blender remote",
 "author": "Gobelet Team: Samuel Bernou, Laure Le Sidaner, Swann Martinez",
 "version": (1, 0),
 "blender": (2, 8, 0),
 "location": "View3D",
 "description": "Allow to use smartphone as a controller",
 "warning": "",
 "wiki_url": "",
 "tracker_url": "",
 "category": "System"}

import bpy

def register():
    import sys

    # Support reloading
    if '%s.blender' % __name__ in sys.modules:
        import importlib

        def reload_mod(name):
            modname = '%s.%s' % (__name__, name)
            try:
                old_module = sys.modules[modname]
            except KeyError:
                # Wasn't loaded before -- can happen after an upgrade.
                new_module = importlib.import_module(modname)
            else:
                new_module = importlib.reload(old_module)

            sys.modules[modname] = new_module
            return new_module

        async_loop = reload_mod('async_loop')
    else:
        from . import (async_loop,)

    async_loop.setup_asyncio_executor()
    async_loop.register()

def unregister():
    from . import (async_loop)
    async_loop.unregister()
