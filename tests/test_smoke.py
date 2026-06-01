from typer.testing import CliRunner

from hopper import __version__
from hopper.cli import app

runner = CliRunner()


def test_version_command_prints_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_app_name():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "hopper" in result.stdout.lower()
