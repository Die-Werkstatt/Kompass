# SPDX-License-Identifier: GPL-3.0-or-later
# aislop-ignore-file hallucinated-import -- bl_ui ships with Blender
"""The one place that reads Blender's tool system.

bl_ui is shipped with Blender but is not documented API, so it can change
between releases without notice. Nothing else in Kompass imports it.
"""


def label(context, space_type, tool_id):
    """The tool's name, or None when it is not available in this context."""
    try:
        from bl_ui.space_toolsystem_common import item_from_id

        item = item_from_id(context, space_type, tool_id)
    # Undocumented code may fail in any way; a pie must still open.
    except Exception:  # noqa: BLE001
        return None
    return None if item is None else item.label
