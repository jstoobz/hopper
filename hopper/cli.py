"""hopper command-line interface."""

import typer

from hopper import __version__

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
    # command registered; add / show / done are layered on top of this.


@app.command()
def version() -> None:
    """Print the hopper version."""
    typer.echo(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
