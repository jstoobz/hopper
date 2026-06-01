"""hopper command-line interface."""

import json
import subprocess
from pathlib import Path

import typer

from hopper import __version__, store

app = typer.Typer(
    name="hopper",
    help="A fast, project-aware todo CLI for hopping between work streams.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root() -> None:
    """A fast, project-aware todo CLI for hopping between work streams."""
    # Empty root callback keeps hopper a multi-command group even with a single
    # command registered; commands below are layered on top of this.


def current_project() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        top = out.stdout.strip()
        if top:
            return Path(top).name
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path.cwd().name


def _selected_priority(flags: dict[str, bool]) -> str | None:
    chosen = [p for p, on in flags.items() if on]
    if len(chosen) > 1:
        typer.echo("error: choose at most one of --p0/--p1/--p2/--p3", err=True)
        raise typer.Exit(2)
    return chosen[0] if chosen else None


def _render(items: list[dict], *, all_projects: bool) -> None:
    for it in items:
        proj = f" ({it['project']})" if all_projects else ""
        mark = "x" if it["status"] == "done" else " "
        typer.echo(f"[{mark}] #{it['id']:>3} {it['priority']}{proj}  {it['text']}")


@app.command()
def add(
    priority: str = typer.Argument(..., help="Priority: P0-P3"),
    text: str = typer.Argument(..., help="What needs doing"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project (default: current)"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t", help="Tag (repeatable)"),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
) -> None:
    """Add a todo to the current (or named) project."""
    priority = priority.upper()
    if priority not in store.PRIORITIES:
        typer.echo(f"error: priority must be one of {', '.join(store.PRIORITIES)}", err=True)
        raise typer.Exit(2)
    item = store.add(
        text=text,
        priority=priority,
        project=project or current_project(),
        tags=tag or [],
    )
    if json_out:
        typer.echo(json.dumps(item))
    else:
        typer.echo(f"added #{item['id']} [{item['priority']}] ({item['project']}): {item['text']}")


@app.command()
def show(
    pattern: str | None = typer.Argument(None, help="Substring filter on todo text"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project (default: current)"),
    all_projects: bool = typer.Option(False, "--all", help="Span all projects"),
    p0: bool = typer.Option(False, "--p0", help="Only P0"),
    p1: bool = typer.Option(False, "--p1", help="Only P1"),
    p2: bool = typer.Option(False, "--p2", help="Only P2"),
    p3: bool = typer.Option(False, "--p3", help="Only P3"),
    done: bool = typer.Option(False, "--done", help="Include closed todos"),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
) -> None:
    """Show todos, ordered by priority (current project by default)."""
    priority = _selected_priority({"P0": p0, "P1": p1, "P2": p2, "P3": p3})
    scope = None if all_projects else (project or current_project())
    items = store.query(
        project=scope,
        priority=priority,
        include_done=done,
        all_projects=all_projects,
    )
    if pattern:
        needle = pattern.lower()
        items = [it for it in items if needle in it["text"].lower()]
    if json_out:
        typer.echo(json.dumps(items))
        return
    if not items:
        typer.echo("no todos" if all_projects else f"no todos for {scope}")
        return
    _render(items, all_projects=all_projects)


@app.command()
def done(
    item_id: int = typer.Argument(..., help="Todo id to close"),
    json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
) -> None:
    """Close a todo by id."""
    item = store.mark_done(item_id)
    if item is None:
        typer.echo(f"error: no todo with id {item_id}", err=True)
        raise typer.Exit(1)
    if json_out:
        typer.echo(json.dumps(item))
    else:
        typer.echo(f"done #{item['id']}: {item['text']}")


@app.command()
def version() -> None:
    """Print the hopper version."""
    typer.echo(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
