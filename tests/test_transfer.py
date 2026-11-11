from dataclasses import replace
from pathlib import Path

from kompass.core import model, transfer

EXAMPLE = model.loads(
    (Path(__file__).parent / "data" / "example.json").read_text(encoding="utf-8")
)
SELECT, MESH = EXAMPLE
EMPTY = (None,) * 8


def test_with_sub_pies_follows_sub_pies():
    assert transfer.with_sub_pies(EXAMPLE, "select") == (SELECT, MESH)
    assert transfer.with_sub_pies(EXAMPLE, "mesh") == (MESH,)


def test_merge_into_nothing_keeps_everything():
    assert transfer.merge((), EXAMPLE, False) == (EXAMPLE, ())


def test_merge_keeps_both_pies_with_one_id():
    # The copies get new ids, the copied sub-pie slot follows, and the copy
    # of Select loses the shortcut that my Select already has.
    pies, unbound = transfer.merge(EXAMPLE, EXAMPLE, False)
    assert [pie.id for pie in pies] == ["select", "mesh", "select-2", "mesh-2"]
    assert pies[:2] == EXAMPLE
    assert pies[2].slots[2] == model.SubPieSlot(pie="mesh-2")
    assert pies[2].shortcut is None
    assert unbound == (SELECT,)
    model.validate(pies)


def test_merge_skips_ids_already_taken():
    own = (*EXAMPLE, model.Pie(id="mesh-2", name="Other", slots=EMPTY))
    pies, _ = transfer.merge(own, (MESH,), False)
    assert [pie.id for pie in pies] == ["select", "mesh", "mesh-2", "mesh-3"]


def test_merge_replaces_when_asked():
    newer = replace(MESH, name="Mesh 2")
    pies, unbound = transfer.merge(EXAMPLE, (replace(SELECT, name="New"), newer), True)
    assert [pie.name for pie in pies] == ["New", "Mesh 2"]
    # The replaced pie's shortcut is free for the pie that replaces it.
    assert pies[0].shortcut == SELECT.shortcut
    assert unbound == ()


def test_merge_unbinds_a_shortcut_used_twice_in_one_file():
    twin = model.Pie(id="twin", name="Twin", slots=EMPTY, shortcut=SELECT.shortcut)
    pies, unbound = transfer.merge((), (*EXAMPLE, twin), False)
    assert pies[2].shortcut is None
    assert unbound == (twin,)
