# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bpy is provided by Blender
"""The stored pies of this Blender profile."""

from pathlib import Path

import bpy

from ..core import store
from . import ADDON

pies = ()
# Why the pie file was not loaded, or None.
problem = None


def path():
    # Blender keeps this directory across upgrades of the extension and
    # deletes it when the extension is uninstalled.
    return Path(bpy.utils.extension_path_user(ADDON, create=True)) / "pies.json"


def load():
    global pies, problem
    pies, problem = store.load(path())


def save(new):
    global pies
    store.save(path(), new)
    pies = new
