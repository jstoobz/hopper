"""Persistence for the hopper backlog store."""

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from filelock import FileLock

SCHEMA_VERSION = 1
PRIORITIES = ("P0", "P1", "P2", "P3")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def store_path() -> Path:
    root = os.environ.get("HOPPER_ROOT")
    if root:
        return Path(root).expanduser() / "backlog.json"
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "hopper" / "backlog.json"


def _empty() -> dict:
    return {"schema_version": SCHEMA_VERSION, "next_id": 1, "items": []}


def load() -> dict:
    path = store_path()
    if not path.exists():
        return _empty()
    return json.loads(path.read_text(encoding="utf-8"))


@contextmanager
def transaction() -> Iterator[dict]:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(f"{path}.lock"):
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else _empty()
        yield data
        tmp = path.with_name(f"{path.name}.tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)


def add(*, text: str, priority: str, project: str, tags: list[str] | None = None) -> dict:
    with transaction() as data:
        item = {
            "id": data["next_id"],
            "project": project,
            "priority": priority,
            "text": text,
            "status": "open",
            "created_at": _now(),
            "done_at": None,
            "tags": tags or [],
        }
        data["next_id"] += 1
        data["items"].append(item)
    return item


def mark_done(item_id: int) -> dict | None:
    with transaction() as data:
        for item in data["items"]:
            if item["id"] == item_id:
                if item["status"] != "done":
                    item["status"] = "done"
                    item["done_at"] = _now()
                return item
    return None


def query(
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    priority: str | None = None,
    include_done: bool = False,
) -> list[dict]:
    items = load()["items"]
    result = [
        it
        for it in items
        if (include_done or it["status"] == "open")
        and (include is None or it["project"] in include)
        and (exclude is None or it["project"] not in exclude)
        and (priority is None or it["priority"] == priority)
    ]
    result.sort(key=lambda it: (it["priority"], it["id"]))
    return result
