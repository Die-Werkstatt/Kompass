import copy
import json
from pathlib import Path

import pytest

from kompass.core import model

EXAMPLE = (Path(__file__).parent / "data" / "example.json").read_text(encoding="utf-8")


def rejected(change):
    """The message from loading the example after change() edited its data."""
    data = copy.deepcopy(json.loads(EXAMPLE))
    change(data)
    with pytest.raises(model.InvalidPieFile) as error:
        model.loads(json.dumps(data))
    return str(error.value)


def test_example_loads():
    select, mesh = model.loads(EXAMPLE)
    assert select.shortcut == model.Shortcut(
        keymap="3D View",
        space_type="VIEW_3D",
        key="Q",
        modifiers=frozenset({"shift", "alt"}),
    )
    assert select.slots[1] == model.ToolSlot(
        space_type="VIEW_3D", tool="builtin.select_lasso", label="Lasso"
    )
    assert select.slots[2] == model.SubPieSlot(pie="mesh")
    assert select.slots[4:] == (None, None, None, None)
    assert mesh.shortcut is None
    assert mesh.slots[1].properties == {"value": [0, 0, 1.0], "snap": False}


def test_dumps_round_trips_the_example():
    assert model.dumps(model.loads(EXAMPLE)) == EXAMPLE


def test_empty_file_loads():
    assert model.loads('{"schema_version": 1, "pies": []}') == ()


def test_invalid_json_is_rejected():
    with pytest.raises(model.InvalidPieFile, match="not valid JSON"):
        model.loads("{")


def test_newer_schema_is_rejected():
    message = rejected(lambda data: data.update(schema_version=2))
    assert "newer Kompass" in message


@pytest.mark.parametrize("version", [0, "1", 1.0, True])
def test_other_schema_versions_are_rejected(version):
    assert "schema_version" in rejected(
        lambda data: data.update(schema_version=version)
    )


def test_missing_field_is_named():
    def change(data):
        del data["pies"][0]["name"]

    assert rejected(change) == 'pies[0]: "name" is missing'


def test_unknown_key_is_named():
    def change(data):
        data["pies"][1]["slots"][0]["idnam"] = "mesh.subdivide"

    assert rejected(change) == 'pies[1].slots[0]: unknown key "idnam"'


def test_unknown_slot_type_is_rejected():
    def change(data):
        data["pies"][0]["slots"][4] = {"type": "python", "code": "import os"}

    assert rejected(change) == 'pies[0].slots[4]: unknown slot type "python"'


def test_wrong_slot_count_is_rejected():
    def change(data):
        data["pies"][0]["slots"].append(None)

    assert rejected(change) == 'pie "select" has 9 slots, expected 4, 8 or 12'


def test_a_pie_of_twelve_slots_round_trips():
    data = json.loads(EXAMPLE)
    data["pies"][0]["slots"] += [None] * 4
    pies = model.loads(json.dumps(data))
    assert len(pies[0].slots) == 12
    assert model.loads(model.dumps(pies)) == pies


def test_slots_of_twelve_are_named_by_number():
    def change(data):
        slots = data["pies"][0]["slots"]
        slots += [None] * 4
        slots[2] = {"type": "sub_pie", "pie": "gone"}

    assert rejected(change) == (
        'pie "select" slot 3 opens the pie "gone", which does not exist'
    )


def test_duplicate_id_is_rejected():
    def change(data):
        data["pies"][1]["id"] = "select"

    assert rejected(change) == 'two pies share the id "select"'


def test_missing_sub_pie_target_is_rejected():
    def change(data):
        data["pies"][0]["slots"][2]["pie"] = "gone"

    assert (
        rejected(change)
        == 'pie "select" slot S opens the pie "gone", which does not exist'
    )


def test_sub_pie_opening_itself_is_rejected():
    def change(data):
        data["pies"][1]["slots"][7] = {"type": "sub_pie", "pie": "mesh"}

    assert rejected(change) == "sub-pies form a loop: mesh > mesh"


def test_sub_pie_loop_is_rejected():
    def change(data):
        data["pies"][1]["slots"][7] = {"type": "sub_pie", "pie": "select"}

    assert rejected(change) == "sub-pies form a loop: select > mesh > select"


def test_shared_sub_pie_is_not_a_loop():
    data = json.loads(EXAMPLE)
    third = copy.deepcopy(data["pies"][0])
    third.update(id="other", name="Other")
    data["pies"].append(third)
    assert len(model.loads(json.dumps(data))) == 3


def test_malformed_operator_idname_is_rejected():
    def change(data):
        data["pies"][1]["slots"][0]["idname"] = "MESH_OT_subdivide"

    assert 'operator "MESH_OT_subdivide"' in rejected(change)


def test_nested_object_property_is_rejected():
    def change(data):
        data["pies"][1]["slots"][0]["properties"]["number_cuts"] = {"a": 1}

    assert 'property "number_cuts"' in rejected(change)


def test_unknown_modifier_is_rejected():
    def change(data):
        data["pies"][0]["shortcut"]["modifiers"] = ["cmd"]

    assert 'unknown modifier "cmd"' in rejected(change)


def test_lowercase_key_is_rejected():
    def change(data):
        data["pies"][0]["shortcut"]["key"] = "q"

    assert 'key "q"' in rejected(change)


def test_dumps_refuses_invalid_pies():
    pie = model.Pie(id="a", name="A", slots=(None,) * 7)
    with pytest.raises(model.InvalidPieFile, match="7 slots"):
        model.dumps((pie,))


# The architecture rule in agent_docs/CLAUDE.md: core runs without Blender.
def test_core_never_imports_bpy():
    core = Path(model.__file__).parent
    for source in core.rglob("*.py"):
        text = source.read_text(encoding="utf-8")
        assert "import bpy" not in text and "from bpy" not in text, source.name


def test_starter_pies_load():
    path = Path(__file__).parent.parent / "kompass" / "starter.json"
    text = path.read_text(encoding="utf-8")
    assert model.dumps(model.loads(text)) == text


def test_a_pie_of_four_slots_round_trips():
    data = json.loads(EXAMPLE)
    data["pies"][0]["slots"] = data["pies"][0]["slots"][:4]
    (select, _) = model.loads(json.dumps(data))
    assert len(select.slots) == 4
    assert model.slot_name(select, 3) == "N"
    assert json.loads(model.dumps(model.loads(json.dumps(data)))) == data
