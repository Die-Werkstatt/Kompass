# SPDX-License-Identifier: GPL-3.0-or-later
"""The pie data model and its JSON file format.

One format serves the stored pie file, export, import and starter pies.
"""

import json
import re
from dataclasses import dataclass, field

SCHEMA_VERSION = 1

# Blender fills a pie menu in this order (radial_dir_order in interface.cc),
# so slot index n of a pie is direction n of this tuple.
SLOT_DIRECTIONS = ("W", "E", "S", "N", "NW", "NE", "SW", "SE")
# A pie has as many slots as Blender's pie menu, or 12, clockwise from north. Only a pie that Kompass draws can show those.
NATIVE_SLOTS = len(SLOT_DIRECTIONS)
WIDE_SLOTS = 12

MODIFIERS = ("ctrl", "shift", "alt", "oskey", "hyper")

_OPERATOR_IDNAME = re.compile(r"[a-z0-9_]+\.[a-z0-9_]+")
_EVENT_TYPE = re.compile(r"[A-Z0-9_]+")


class InvalidPieFile(ValueError):
    """The file or the pies break a rule of the format; the message names it."""


@dataclass(frozen=True)
class ToolSlot:
    space_type: str
    tool: str
    label: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class OperatorSlot:
    idname: str
    properties: dict = field(default_factory=dict)
    label: str | None = None
    icon: str | None = None


@dataclass(frozen=True)
class SubPieSlot:
    pie: str
    label: str | None = None
    icon: str | None = None


Slot = ToolSlot | OperatorSlot | SubPieSlot


@dataclass(frozen=True)
class Shortcut:
    # KeyMaps.new() needs the space type next to the keymap name: "3D View"
    # lives in VIEW_3D, "Object Mode" in EMPTY.
    keymap: str
    space_type: str
    key: str
    modifiers: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Pie:
    id: str
    name: str
    slots: tuple[Slot | None, ...]
    # A pie that only opens as a sub-pie has no shortcut.
    shortcut: Shortcut | None = None


# --- validation -------------------------------------------------------------


def validate(pies):
    """Raise InvalidPieFile for the first rule the pies break."""
    ids = set()
    for pie in pies:
        if not pie.id:
            raise InvalidPieFile(f'pie "{pie.name}" has an empty id')
        if pie.id in ids:
            raise InvalidPieFile(f'two pies share the id "{pie.id}"')
        ids.add(pie.id)
    for pie in pies:
        _validate_pie(pie, ids)
    _reject_sub_pie_loops(pies)


def _validate_pie(pie, ids):
    where = f'pie "{pie.id}"'
    if not pie.name:
        raise InvalidPieFile(f"{where} has an empty name")
    if len(pie.slots) not in {NATIVE_SLOTS, WIDE_SLOTS}:
        raise InvalidPieFile(
            f"{where} has {len(pie.slots)} slots, expected {NATIVE_SLOTS} or "
            f"{WIDE_SLOTS}"
        )
    if pie.shortcut is not None:
        _validate_shortcut(pie.shortcut, where)
    for index, slot in enumerate(pie.slots):
        if slot is not None:
            _validate_slot(slot, f"{where} slot {slot_name(pie, index)}", ids)


def slot_name(pie, index):
    if len(pie.slots) == NATIVE_SLOTS:
        return SLOT_DIRECTIONS[index]
    # Numbered clockwise from north, which is 1.
    return str(index + 1)


def _validate_shortcut(shortcut, where):
    if not shortcut.keymap or not shortcut.space_type:
        raise InvalidPieFile(f"{where} shortcut has no keymap or space type")
    if not _EVENT_TYPE.fullmatch(shortcut.key):
        raise InvalidPieFile(
            f'{where} shortcut key "{shortcut.key}" is not a Blender event type'
        )
    unknown = sorted(set(shortcut.modifiers) - set(MODIFIERS))
    if unknown:
        raise InvalidPieFile(
            f'{where} shortcut has the unknown modifier "{unknown[0]}"'
        )


def _validate_slot(slot, where, ids):
    if isinstance(slot, ToolSlot):
        if not slot.space_type or not slot.tool:
            raise InvalidPieFile(f"{where} has no tool or space type")
    elif isinstance(slot, OperatorSlot):
        if not _OPERATOR_IDNAME.fullmatch(slot.idname):
            raise InvalidPieFile(
                f'{where} operator "{slot.idname}" is not of the form "module.name"'
            )
        for name, value in slot.properties.items():
            if not _is_property_value(value):
                raise InvalidPieFile(
                    f'{where} property "{name}" is not a number, a boolean, text '
                    "or a list of those"
                )
    elif slot.pie not in ids:
        raise InvalidPieFile(
            f'{where} opens the pie "{slot.pie}", which does not exist'
        )


def _is_property_value(value):
    if isinstance(value, list):
        return all(_is_property_value(item) for item in value)
    return isinstance(value, (bool, int, float, str))


def _reject_sub_pie_loops(pies):
    opens = {
        pie.id: [slot.pie for slot in pie.slots if isinstance(slot, SubPieSlot)]
        for pie in pies
    }
    # A pie is cleared once everything reachable from it is known to end.
    cleared = set()

    def walk(pie_id, trail):
        if pie_id in trail:
            loop = " > ".join([*trail[trail.index(pie_id) :], pie_id])
            raise InvalidPieFile(f"sub-pies form a loop: {loop}")
        if pie_id in cleared:
            return
        for target in opens[pie_id]:
            walk(target, [*trail, pie_id])
        cleared.add(pie_id)

    for pie_id in opens:
        walk(pie_id, [])


# --- reading ----------------------------------------------------------------


def loads(text):
    """Parse the text of a pie file into a validated tuple of pies."""
    try:
        data = json.loads(text)
    except ValueError as error:
        raise InvalidPieFile(f"not valid JSON: {error}") from error
    _expect_keys(data, "file", required=("schema_version", "pies"))
    version = data["schema_version"]
    if type(version) is not int:
        raise InvalidPieFile("schema_version: expected a whole number")
    if version > SCHEMA_VERSION:
        raise InvalidPieFile(
            f"schema_version {version} was written by a newer Kompass; "
            f"this one reads up to {SCHEMA_VERSION}"
        )
    if version < SCHEMA_VERSION:
        raise InvalidPieFile(f"schema_version {version} is not a known version")
    if not isinstance(data["pies"], list):
        raise InvalidPieFile("pies: expected a list")
    pies = tuple(_read_pie(item, f"pies[{i}]") for i, item in enumerate(data["pies"]))
    validate(pies)
    return pies


def _expect_keys(value, path, required, optional=()):
    if not isinstance(value, dict):
        raise InvalidPieFile(f"{path}: expected an object")
    for key in required:
        if key not in value:
            raise InvalidPieFile(f'{path}: "{key}" is missing')
    # Unknown keys are refused so that a typo in a hand-edited file is not
    # silently dropped on the next save.
    for key in value:
        if key not in required and key not in optional:
            raise InvalidPieFile(f'{path}: unknown key "{key}"')


def _text(value, path):
    if not isinstance(value, str):
        raise InvalidPieFile(f"{path}: expected text")
    return value


def _optional_text(obj, key, path):
    return None if obj.get(key) is None else _text(obj[key], f"{path}.{key}")


def _read_pie(data, path):
    _expect_keys(data, path, required=("id", "name", "slots"), optional=("shortcut",))
    if not isinstance(data["slots"], list):
        raise InvalidPieFile(f"{path}.slots: expected a list")
    return Pie(
        id=_text(data["id"], f"{path}.id"),
        name=_text(data["name"], f"{path}.name"),
        slots=tuple(
            _read_slot(item, f"{path}.slots[{i}]")
            for i, item in enumerate(data["slots"])
        ),
        shortcut=_read_shortcut(data.get("shortcut"), f"{path}.shortcut"),
    )


def _read_shortcut(data, path):
    if data is None:
        return None
    _expect_keys(
        data, path, required=("keymap", "space_type", "key"), optional=("modifiers",)
    )
    modifiers = data.get("modifiers", [])
    if not isinstance(modifiers, list):
        raise InvalidPieFile(f"{path}.modifiers: expected a list")
    return Shortcut(
        keymap=_text(data["keymap"], f"{path}.keymap"),
        space_type=_text(data["space_type"], f"{path}.space_type"),
        key=_text(data["key"], f"{path}.key"),
        modifiers=frozenset(_text(item, f"{path}.modifiers") for item in modifiers),
    )


def _read_slot(data, path):
    if data is None:
        return None
    if not isinstance(data, dict) or "type" not in data:
        raise InvalidPieFile(f'{path}: expected null or an object with a "type"')
    kind = data["type"]
    shared = ("type", "label", "icon")
    label = _optional_text(data, "label", path)
    icon = _optional_text(data, "icon", path)
    if kind == "tool":
        _expect_keys(
            data, path, required=("type", "space_type", "tool"), optional=shared
        )
        return ToolSlot(
            space_type=_text(data["space_type"], f"{path}.space_type"),
            tool=_text(data["tool"], f"{path}.tool"),
            label=label,
            icon=icon,
        )
    if kind == "operator":
        _expect_keys(
            data, path, required=("type", "idname"), optional=(*shared, "properties")
        )
        properties = data.get("properties", {})
        if not isinstance(properties, dict):
            raise InvalidPieFile(f"{path}.properties: expected an object")
        return OperatorSlot(
            idname=_text(data["idname"], f"{path}.idname"),
            properties=properties,
            label=label,
            icon=icon,
        )
    if kind == "sub_pie":
        _expect_keys(data, path, required=("type", "pie"), optional=shared)
        return SubPieSlot(pie=_text(data["pie"], f"{path}.pie"), label=label, icon=icon)
    raise InvalidPieFile(f'{path}: unknown slot type "{kind}"')


# --- writing ----------------------------------------------------------------


def dumps(pies):
    """Return the text of a pie file for pies that pass validate()."""
    validate(pies)
    data = {"schema_version": SCHEMA_VERSION, "pies": [_write_pie(pie) for pie in pies]}
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _write_pie(pie):
    data = {"id": pie.id, "name": pie.name}
    if pie.shortcut is not None:
        data["shortcut"] = {
            "keymap": pie.shortcut.keymap,
            "space_type": pie.shortcut.space_type,
            "key": pie.shortcut.key,
            # In MODIFIERS order so the same pie always writes the same text.
            "modifiers": [name for name in MODIFIERS if name in pie.shortcut.modifiers],
        }
    data["slots"] = [None if slot is None else _write_slot(slot) for slot in pie.slots]
    return data


def _write_slot(slot):
    if isinstance(slot, ToolSlot):
        data = {"type": "tool", "space_type": slot.space_type, "tool": slot.tool}
    elif isinstance(slot, OperatorSlot):
        data = {"type": "operator", "idname": slot.idname}
        if slot.properties:
            data["properties"] = slot.properties
    else:
        data = {"type": "sub_pie", "pie": slot.pie}
    if slot.label is not None:
        data["label"] = slot.label
    if slot.icon is not None:
        data["icon"] = slot.icon
    return data
