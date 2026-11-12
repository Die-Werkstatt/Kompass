# SPDX-License-Identifier: GPL-3.0-or-later
"""Changes to the stored pies. Each returns new pies and leaves the old."""

import re
from dataclasses import replace

from .layout import bearings
from .model import NATIVE_SLOTS, Pie, SubPieSlot, slot_name


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
    return (*pies, Pie(id=pie_id, name=name, slots=(None,) * NATIVE_SLOTS))


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


def place(pies, pie_id, slot, content):
    """Return the pies with that slot of the pie holding content, or empty."""
    return _placed(pies, pie_id, {slot: content})


def swap(pies, slot, other):
    """Return the pies with the contents of two slots exchanged.

    Each slot is the id of its pie and its index there.
    """
    held = {
        place: next(pie.slots for pie in pies if pie.id == place[0])[place[1]]
        for place in (slot, other)
    }
    pies = _placed(pies, slot[0], {slot[1]: held[other]})
    return _placed(pies, other[0], {other[1]: held[slot]})


def _placed(pies, pie_id, contents):
    return tuple(
        replace(
            pie,
            slots=tuple(
                contents.get(index, slot) for index, slot in enumerate(pie.slots)
            ),
        )
        if pie.id == pie_id
        else pie
        for pie in pies
    )


def resize(pies, pie_id, count):
    """Return the pies with the pie at that many slots, each content in the
    slot of its old direction.

    Raises ValueError when a slot that has no such direction left is filled.
    """
    pie = next(pie for pie in pies if pie.id == pie_id)
    places = bearings(count)
    slots = [None] * count
    for index, (bearing, content) in enumerate(
        zip(bearings(len(pie.slots)), pie.slots)
    ):
        # A diagonal is 51 degrees in a pie of 8 and 42 in a pie of 12.
        near = min(range(count), key=lambda place: _turn(places[place], bearing))
        if _turn(places[near], bearing) <= 10:
            slots[near] = content
        elif content is not None:
            raise ValueError(
                f"slot {slot_name(pie, index)} has no place in a pie of {count} slots"
            )
    return tuple(
        replace(other, slots=tuple(slots)) if other is pie else other for other in pies
    )


def _turn(bearing, other):
    """Return the degrees between two bearings, at most 180."""
    return abs((bearing - other + 180) % 360 - 180)


def bind(pies, pie_id, shortcut):
    """Return the pies with that shortcut on the pie, or none for None."""
    return tuple(
        replace(pie, shortcut=shortcut) if pie.id == pie_id else pie for pie in pies
    )
