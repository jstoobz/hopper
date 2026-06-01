import json

import pytest

from hopper import store


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("HOPPER_ROOT", str(tmp_path))
    return tmp_path


def test_store_path_respects_hopper_root(root):
    assert store.store_path() == root / "backlog.json"


def test_store_path_xdg_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("HOPPER_ROOT", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert store.store_path() == tmp_path / "hopper" / "backlog.json"


def test_add_increments_ids_and_persists(root):
    a = store.add(text="first", priority="P1", project="proj")
    b = store.add(text="second", priority="P0", project="proj")
    assert (a["id"], b["id"]) == (1, 2)
    assert a["status"] == "open"
    assert a["done_at"] is None
    data = json.loads((root / "backlog.json").read_text())
    assert data["next_id"] == 3
    assert len(data["items"]) == 2


def test_ids_never_reused_after_done(root):
    a = store.add(text="a", priority="P1", project="proj")
    store.mark_done(a["id"])
    b = store.add(text="b", priority="P1", project="proj")
    assert b["id"] == 2


def test_done_marks_done(root):
    item = store.add(text="x", priority="P2", project="proj")
    updated = store.mark_done(item["id"])
    assert updated["status"] == "done"
    assert updated["done_at"] is not None


def test_done_unknown_returns_none(root):
    assert store.mark_done(999) is None


def test_query_excludes_done_by_default(root):
    store.add(text="open one", priority="P1", project="proj")
    closed = store.add(text="closed one", priority="P1", project="proj")
    store.mark_done(closed["id"])
    assert [it["text"] for it in store.query(project="proj")] == ["open one"]
    assert len(store.query(project="proj", include_done=True)) == 2


def test_query_sorts_by_priority_then_id(root):
    store.add(text="p2", priority="P2", project="proj")
    store.add(text="p0", priority="P0", project="proj")
    assert [it["priority"] for it in store.query(project="proj")] == ["P0", "P2"]


def test_query_scopes_by_project_or_all(root):
    store.add(text="a", priority="P1", project="alpha")
    store.add(text="b", priority="P1", project="beta")
    assert len(store.query(project="alpha")) == 1
    assert len(store.query(all_projects=True)) == 2
