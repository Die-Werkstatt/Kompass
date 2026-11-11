# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Everything that needs Blender."""

import bpy

# The add-on's identifier is the package above this one.
ADDON = __package__.rpartition(".")[0]

# These read ADDON while they load.
from . import files, keymaps, pie, preferences, storage

_CLASSES = (
    preferences.KompassPreferences,
    pie.KOMPASS_OT_pie_open,
    files.KOMPASS_OT_pies_export,
    files.KOMPASS_OT_pies_import,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    storage.load()
    keymaps.register()


def unregister():
    keymaps.unregister()
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
