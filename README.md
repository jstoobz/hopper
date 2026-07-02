# hopper

A fast, project-aware todo CLI for hopping between work streams. Add, show, and close
todos from any directory — hopper figures out which project you're in.

## Install

```bash
uv tool install hopper      # or: pipx install hopper
```

Or run without installing:

```bash
uvx hopper show
```

## Usage

```bash
hopper add P1 "wire up OTEL spans"          # add a todo to the current project
hopper add P0 "fix login crash" --project tend
hopper add P2 "random idea" -i               # stash it in the inbox instead
hopper show                                  # open todos for the current project, by priority
hopper show --all                            # across all projects, inbox included
hopper show --include tend,hopper            # a named subset of projects
hopper show --exclude inbox                  # every project except the inbox
hopper show --p0                             # only P0s
hopper done 3                                # close todo #3
hopper jump 3 --project tend                 # move todo #3 into another project
hopper jump 3 -i                             # ...or into the inbox
```

Priorities are `P0`–`P3`. The current project defaults to the git repository (or
directory) you're in; override it with `--project`, or use `-i`/`--inbox` as a
shortcut for `--project inbox` — the catch-all for stray todos.

## JSON output

Every command accepts `--json` for machine-readable output, so other tools can build on
hopper without coupling to it:

```bash
hopper show --all --json
```

The JSON shape is the integration contract — stable across releases within a major version.

## Where data lives

Todos live in a single JSON file under your XDG data directory —
`${XDG_DATA_HOME:-~/.local/share}/hopper/backlog.json`. Set `HOPPER_ROOT` to put it
somewhere else.

## Development

```bash
uv run pytest          # tests
uv run ruff check      # lint
uv run ruff format     # format
```

VSCode: install the **Ruff** (`charliermarsh.ruff`) and **Python** (Pylance) extensions —
formatting and import sorting are wired in `.vscode/settings.json`.

## License

MIT
