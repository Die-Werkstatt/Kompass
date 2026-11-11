from pathlib import Path

import pytest

from kompass.core import model, store

EXAMPLE = Path(__file__).parent / "data" / "example.json"


def test_missing_file_is_no_pies_and_no_problem(tmp_path):
    assert store.load(tmp_path / "pies.json") == ((), None)


def test_save_then_load_returns_the_same_pies(tmp_path):
    pies = model.loads(EXAMPLE.read_text(encoding="utf-8"))
    path = tmp_path / "pies.json"
    store.save(path, pies)
    assert store.load(path) == (pies, None)
    assert [file.name for file in tmp_path.iterdir()] == ["pies.json"]


@pytest.mark.parametrize("content", [b"{", b"\xff\xfe", b'{"schema_version": 2}'])
def test_unreadable_file_is_moved_aside(tmp_path, content):
    path = tmp_path / "pies.json"
    path.write_bytes(content)
    pies, problem = store.load(path)
    assert pies == ()
    assert not path.exists()
    (kept,) = tmp_path.glob("pies.invalid-*.json")
    assert kept.read_bytes() == content
    assert kept.name in problem


def test_file_that_cannot_be_opened_is_left_alone(tmp_path):
    path = tmp_path / "pies.json"
    path.mkdir()
    pies, problem = store.load(path)
    assert pies == ()
    assert "could not be opened" in problem
    assert path.exists()


def test_invalid_pies_do_not_touch_the_file(tmp_path):
    path = tmp_path / "pies.json"
    path.write_bytes(EXAMPLE.read_bytes())
    broken = (model.Pie(id="a", name="A", slots=()),)
    with pytest.raises(model.InvalidPieFile):
        store.save(path, broken)
    assert path.read_bytes() == EXAMPLE.read_bytes()
    assert [file.name for file in tmp_path.iterdir()] == ["pies.json"]
