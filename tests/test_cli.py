import json

import pytest
from typer.testing import CliRunner

from hopper.cli import app

runner = CliRunner()


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("HOPPER_ROOT", str(tmp_path))
    return tmp_path


def test_add_show_done_roundtrip(root):
    added = runner.invoke(app, ["add", "P1", "wire OTEL", "--project", "tend"])
    assert added.exit_code == 0
    assert "#1" in added.stdout

    shown = runner.invoke(app, ["show", "--project", "tend"])
    assert shown.exit_code == 0
    assert "wire OTEL" in shown.stdout

    closed = runner.invoke(app, ["done", "1"])
    assert closed.exit_code == 0

    after = runner.invoke(app, ["show", "--project", "tend"])
    assert "wire OTEL" not in after.stdout


def test_add_rejects_bad_priority(root):
    result = runner.invoke(app, ["add", "P9", "nope", "--project", "x"])
    assert result.exit_code == 2


def test_add_normalizes_priority_case(root):
    result = runner.invoke(app, ["add", "p0", "lower", "--project", "x"])
    assert result.exit_code == 0
    items = json.loads(runner.invoke(app, ["show", "--project", "x", "--json"]).stdout)
    assert items[0]["priority"] == "P0"


def test_show_json_is_machine_readable(root):
    runner.invoke(app, ["add", "P0", "thing", "--project", "x"])
    result = runner.invoke(app, ["show", "--project", "x", "--json"])
    assert result.exit_code == 0
    items = json.loads(result.stdout)
    assert items[0]["text"] == "thing"


def test_show_priority_filter(root):
    runner.invoke(app, ["add", "P0", "urgent", "--project", "x"])
    runner.invoke(app, ["add", "P2", "later", "--project", "x"])
    result = runner.invoke(app, ["show", "--project", "x", "--p0"])
    assert "urgent" in result.stdout
    assert "later" not in result.stdout


def test_show_rejects_multiple_priority_flags(root):
    result = runner.invoke(app, ["show", "--project", "x", "--p0", "--p1"])
    assert result.exit_code == 2


def test_done_unknown_id_errors(root):
    result = runner.invoke(app, ["done", "42"])
    assert result.exit_code == 1
