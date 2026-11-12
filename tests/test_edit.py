from pathlib import Path

import pytest

from kompass.core import edit, model

EXAMPLE = model.loads(
    (Path(__file__).parent / "data" / "example.json").read_text(encoding="utf-8")
)
SELECT, MESH = EXAMPLE


def test_add_appends_an_empty_pie_with_an_id_from_its_name():
    pies = edit.add(EXAMPLE, "Edge Tools!")
    assert pies[:2] == EXAMPLE
    assert (pies[2].id, pies[2].name) == ("edge-tools", "Edge Tools!")
    assert pies[2].slots == (None,) * 8
    assert pies[2].shortcut is None
    model.validate(pies)


def test_add_finds_a_free_id():
    pies = edit.add(edit.add(EXAMPLE, "Mesh"), "Mesh")
    assert [pie.id for pie in pies] == ["select", "mesh", "mesh-2", "mesh-3"]
    assert edit.add((), "???")[0].id == "pie"


def test_rename_changes_the_name_only():
    pies = edit.rename(EXAMPLE, "mesh", "Edit")
    assert [(pie.id, pie.name) for pie in pies] == [
        ("select", "Select"),
        ("mesh", "Edit"),
    ]
    assert pies[1].slots == MESH.slots


def test_duplicate_puts_an_unbound_copy_after_the_pie():
    pies = edit.duplicate(EXAMPLE, "select")
    assert [pie.id for pie in pies] == ["select", "select-2", "mesh"]
    assert pies[1].name == "Select Copy"
    assert pies[1].slots == SELECT.slots
    assert pies[1].shortcut is None
    model.validate(pies)


def test_delete_empties_the_slots_that_opened_the_pie():
    (left,) = edit.delete(EXAMPLE, "mesh")
    assert left.id == "select"
    assert left.slots[2] is None
    assert left.slots[:2] == SELECT.slots[:2]
    model.validate((left,))


def test_place_fills_or_empties_one_slot():
    pies = edit.place(EXAMPLE, "select", 0, None)
    assert pies[0].slots == (None, *SELECT.slots[1:])
    assert pies[1] is MESH
    model.validate(pies)
    subdivide = model.OperatorSlot("mesh.subdivide")
    pies = edit.place(pies, "select", 0, subdivide)
    assert pies[0].slots == (subdivide, *SELECT.slots[1:])
    model.validate(pies)


def test_bind_sets_and_removes_a_shortcut():
    shortcut = model.Shortcut("Mesh", "EMPTY", "K", frozenset({"ctrl"}))
    pies = edit.bind(EXAMPLE, "mesh", shortcut)
    assert pies[1].shortcut == shortcut and pies[0] is SELECT
    model.validate(pies)
    assert edit.bind(pies, "mesh", None)[1].shortcut is None


def test_swap_exchanges_two_slots():
    pies = edit.swap(EXAMPLE, ("select", 0), ("select", 5))
    assert pies[0].slots[0] == SELECT.slots[5]
    assert pies[0].slots[5] == SELECT.slots[0]
    assert [pies[0].slots[n] for n in (1, 2, 3, 4, 6, 7)] == [
        SELECT.slots[n] for n in (1, 2, 3, 4, 6, 7)
    ]
    assert edit.swap(pies, ("select", 5), ("select", 0)) == EXAMPLE


def test_swap_exchanges_slots_of_two_pies():
    pies = edit.swap(EXAMPLE, ("select", 0), ("mesh", 7))
    assert pies[0].slots[0] == EXAMPLE[1].slots[7]
    assert pies[1].slots[7] == SELECT.slots[0]
    model.validate(pies)
    assert edit.swap(pies, ("mesh", 7), ("select", 0)) == EXAMPLE


def test_resize_keeps_each_slot_in_its_direction():
    wide = edit.resize(EXAMPLE, "select", 12)[0]
    # West, east, south and north of 8 are slots 10, 4, 7 and 1 of 12.
    assert [wide.slots[index] for index in (9, 3, 6, 0)] == list(SELECT.slots[:4])
    assert sum(slot is not None for slot in wide.slots) == 4
    assert edit.resize((wide, MESH), "select", 8) == EXAMPLE


def test_resize_refuses_to_drop_a_filled_slot():
    wide = edit.resize(EXAMPLE, "select", 12)
    # Slot 3 of 12 lies at 68 degrees, where a pie of 8 has nothing.
    filled = edit.place(wide, "select", 2, SELECT.slots[0])
    with pytest.raises(ValueError, match="slot 3 has no place in a pie of 8 slots"):
        edit.resize(filled, "select", 8)
