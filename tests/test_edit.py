from pathlib import Path

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
