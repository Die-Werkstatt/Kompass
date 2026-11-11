# SPDX-License-Identifier: GPL-3.0-or-later
"""Changes to the stored pies. Each returns new pies and leaves the old."""

import re
from dataclasses import replace

from .model import SLOT_DIRECTIONS, Pie, SubPieSlot


def free_id(wanted, taken):
    """Return wanted, or wanted with the first number that makes it new."""
    if wanted not in taken:
        return wanted
    number = 2
    while f"{wanted}-{number}" in taken:
        number += 1
    return f"{wanted}-{number}"


def add(pies, name):
    """Return the pies with a new, empty pie of that name at the end."""
    wanted = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "pie"
    pie_id = free_id(wanted, {pie.id for pie in pies})
    return (*pies, Pie(id=pie_id, name=name, slots=(None,) * len(SLOT_DIRECTIONS)))


def rename(pies, pie_id, name):
    return tuple(replace(pie, name=name) if pie.id == pie_id else pie for pie in pies)


def duplicate(pies, pie_id):
    """Return the pies with a copy of the pie right after it.

    The copy has no shortcut: Blender would only ever open the first of two
    pies on one shortcut.
    """
    result = []
    for pie in pies:
        result.append(pie)
        if pie.id == pie_id:
            copy_id = free_id(pie.id, {other.id for other in pies})
            name = f"{pie.name} Copy"
            result.append(replace(pie, id=copy_id, name=name, shortcut=None))
    return tuple(result)


def delete(pies, pie_id):
    """Return the pies without that pie, and empty the slots that opened it."""
    return tuple(
        replace(
            pie,
            slots=tuple(
                None if isinstance(slot, SubPieSlot) and slot.pie == pie_id else slot
                for slot in pie.slots
            ),
        )
        for pie in pies
        if pie.id != pie_id
    )
