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


def test_add_inbox_flag_sets_project(root):
    result = runner.invoke(app, ["add", "P1", "stray thought", "-i"])
    assert result.exit_code == 0
    items = json.loads(runner.invoke(app, ["show", "--project", "inbox", "--json"]).stdout)
    assert items[0]["project"] == "inbox"


def test_add_inbox_long_flag_matches_short(root):
    result = runner.invoke(app, ["add", "P1", "via long flag", "--inbox"])
    assert result.exit_code == 0
    items = json.loads(runner.invoke(app, ["show", "--project", "inbox", "--json"]).stdout)
    assert items[0]["text"] == "via long flag"


def test_add_rejects_project_and_inbox_together(root):
    result = runner.invoke(app, ["add", "P1", "conflict", "--project", "foo", "-i"])
    assert result.exit_code == 2


def test_show_inbox_flag_scopes_to_inbox(root):
    runner.invoke(app, ["add", "P1", "in inbox", "-i"])
    runner.invoke(app, ["add", "P1", "in alpha", "--project", "alpha"])
    shown = runner.invoke(app, ["show", "-i"])
    assert "in inbox" in shown.stdout
    assert "in alpha" not in shown.stdout


def test_show_all_includes_inbox(root):
    runner.invoke(app, ["add", "P1", "in inbox", "-i"])
    runner.invoke(app, ["add", "P1", "in alpha", "--project", "alpha"])
    shown = runner.invoke(app, ["show", "--all"])
    assert "in inbox" in shown.stdout
    assert "in alpha" in shown.stdout


def test_show_include_selects_subset(root):
    runner.invoke(app, ["add", "P1", "a item", "--project", "alpha"])
    runner.invoke(app, ["add", "P1", "b item", "--project", "beta"])
    runner.invoke(app, ["add", "P1", "g item", "--project", "gamma"])
    shown = runner.invoke(app, ["show", "--include", "alpha,beta"])
    assert "a item" in shown.stdout
    assert "b item" in shown.stdout
    assert "g item" not in shown.stdout


def test_show_exclude_inbox_is_project_only_view(root):
    runner.invoke(app, ["add", "P1", "in inbox", "-i"])
    runner.invoke(app, ["add", "P1", "in alpha", "--project", "alpha"])
    shown = runner.invoke(app, ["show", "--exclude", "inbox"])
    assert "in alpha" in shown.stdout
    assert "in inbox" not in shown.stdout


def test_show_rejects_multiple_scope_selectors(root):
    result = runner.invoke(app, ["show", "--all", "--include", "alpha"])
    assert result.exit_code == 2


def test_show_rejects_project_and_inbox_together(root):
    result = runner.invoke(app, ["show", "--project", "foo", "-i"])
    assert result.exit_code == 2


def test_show_rejects_project_and_include_together(root):
    result = runner.invoke(app, ["show", "--project", "foo", "--include", "bar"])
    assert result.exit_code == 2


def test_jump_moves_todo_to_named_project(root):
    runner.invoke(app, ["add", "P1", "stray", "--project", "alpha"])
    result = runner.invoke(app, ["jump", "1", "--project", "beta"])
    assert result.exit_code == 0
    items = json.loads(runner.invoke(app, ["show", "--project", "beta", "--json"]).stdout)
    assert items[0]["text"] == "stray"


def test_jump_inbox_flag_moves_to_inbox(root):
    runner.invoke(app, ["add", "P1", "stray", "--project", "alpha"])
    result = runner.invoke(app, ["jump", "1", "-i"])
    assert result.exit_code == 0
    items = json.loads(runner.invoke(app, ["show", "-i", "--json"]).stdout)
    assert items[0]["text"] == "stray"


def test_jump_requires_destination(root):
    runner.invoke(app, ["add", "P1", "stray", "--project", "alpha"])
    result = runner.invoke(app, ["jump", "1"])
    assert result.exit_code == 2


def test_jump_rejects_project_and_inbox_together(root):
    runner.invoke(app, ["add", "P1", "stray", "--project", "alpha"])
    result = runner.invoke(app, ["jump", "1", "--project", "beta", "-i"])
    assert result.exit_code == 2


def test_jump_unknown_id_errors(root):
    result = runner.invoke(app, ["jump", "999", "-i"])
    assert result.exit_code == 1


def test_jump_json_output(root):
    runner.invoke(app, ["add", "P1", "stray", "--project", "alpha"])
    result = runner.invoke(app, ["jump", "1", "--project", "beta", "--json"])
    item = json.loads(result.stdout)
    assert item["project"] == "beta"


def test_root_help_has_examples_section():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Examples" in result.stdout


def test_done_help_notes_ids_are_global():
    result = runner.invoke(app, ["done", "--help"])
    assert result.exit_code == 0
    assert "global" in result.stdout.lower()
