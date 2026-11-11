# SPDX-License-Identifier: GPL-3.0-or-later
"""Kompass: user-defined pie menus, each on its own shortcut."""


# Everything that needs Blender is imported here, not at the top, so that the
# package itself imports without it.
def register():
    from . import blender

    blender.register()


def unregister():
    from . import blender

    blender.unregister()
