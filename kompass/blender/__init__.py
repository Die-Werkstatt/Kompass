# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""Everything that needs Blender."""

import bpy

# The add-on's identifier is the package above this one.
ADDON = __package__.rpartition(".")[0]

# These read ADDON while they load.
from . import preferences, storage


def register():
    bpy.utils.register_class(preferences.KompassPreferences)
    storage.load()


def unregister():
    bpy.utils.unregister_class(preferences.KompassPreferences)
