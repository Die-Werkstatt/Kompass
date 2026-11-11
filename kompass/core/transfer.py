# SPDX-License-Identifier: GPL-3.0-or-later
"""Choosing pies for export and adding imported pies to the stored ones."""

from dataclasses import replace

from .edit import free_id
from .model import SubPieSlot


def with_sub_pies(pies, pie_id):
    """Return the pie with that id and every pie it opens, in stored order."""
    opens = {
        pie.id: [slot.pie for slot in pie.slots if isinstance(slot, SubPieSlot)]
        for pie in pies
    }
    wanted, queue = set(), [pie_id]
    while queue:
        current = queue.pop()
        if current not in wanted:
            wanted.add(current)
            queue += opens[current]
    return tuple(pie for pie in pies if pie.id in wanted)


def merge(own, incoming, replace_own):
    """Return own with incoming added, and the incoming pies left unbound.

    An incoming pie whose id is already in own replaces that pie when
    replace_own is set and gets a new id otherwise. An incoming pie whose
    shortcut another pie already has loses it: Blender would only ever open
    the first of the two.
    """
    merged = {pie.id: pie for pie in own}
    incoming_ids = {pie.id for pie in incoming}
    new_ids = {}
    if not replace_own:
        taken = set(merged) | incoming_ids
        for pie_id in incoming_ids & set(merged):
            new_ids[pie_id] = free_id(pie_id, taken)
            taken.add(new_ids[pie_id])
    used = {
        pie.shortcut
        for pie in own
        if pie.shortcut and not (replace_own and pie.id in incoming_ids)
    }
    unbound = []
    for pie in incoming:
        shortcut = pie.shortcut
        if shortcut in used:
            shortcut = None
            unbound.append(pie)
        elif shortcut:
            used.add(shortcut)
        slots = tuple(
            replace(slot, pie=new_ids.get(slot.pie, slot.pie))
            if isinstance(slot, SubPieSlot)
            else slot
            for slot in pie.slots
        )
        pie_id = new_ids.get(pie.id, pie.id)
        merged[pie_id] = replace(pie, id=pie_id, slots=slots, shortcut=shortcut)
    return tuple(merged.values()), tuple(unbound)
