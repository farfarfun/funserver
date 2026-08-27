"""Lightweight smoke tests for funserver.

These tests only check that the package imports cleanly and that its public
surface (BaseServer / BaseCommandServer / server_parser and the CLI) behaves
sanely with trivial inputs. They deliberately avoid binding real network
ports, spawning real processes, or touching a user's real home directory.
"""
import subprocess
import sys

import pytest


def test_import_top_level():
    """`import funserver` must succeed (repo/import/PyPI name are all `funserver`)."""
    import funserver  # noqa: F401


def test_import_servers_subpackage():
    """`funserver.servers` package itself imports cleanly.

    Note: `funserver/servers/__init__.py` is empty -- it does not re-export
    BaseServer/BaseCommandServer/server_parser, even though the sibling
    `funserver/servers/base/__init__.py` does re-export them from
    `funserver.servers.base.base`. So the actual public import path is
    `funserver.servers.base`, not `funserver.servers`.
    """
    import funserver.servers  # noqa: F401


def test_import_public_classes():
    """The real public surface lives at funserver.servers.base."""
    from funserver.servers.base import BaseCommandServer, BaseServer, server_parser

    assert BaseServer is not None
    assert BaseCommandServer is not None
    assert callable(server_parser)


def test_base_command_server_construct(tmp_path, monkeypatch):
    """Construct BaseCommandServer with trivial args; redirect HOME so it
    doesn't write into the real user's ~/.cache during tests."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")

    assert server.server_name == "smoke-test-server"
    assert server.port == -1
    assert str(tmp_path) in server.dir_path
    # __init__ should have created its cache/log dirs under the fake HOME.
    import os

    assert os.path.isdir(server.dir_path)
    assert os.path.isdir(f"{server.dir_path}/logs")
    assert server.run_path == f"{tmp_path}/opt/smoke-test-server"


def test_base_command_server_start_stop(tmp_path, monkeypatch):
    """start()/stop() are overridden on BaseCommandServer to just log, so
    they're safe to call directly without touching real processes."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")
    # Should not raise.
    server.start()
    server.stop()


def test_base_command_server_save_pid(tmp_path, monkeypatch):
    """_save_pid() writes the current pid to a file; verify it does so under
    the isolated HOME directory rather than touching real system paths."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")
    server._save_pid()

    with open(server.pid_path) as f:
        content = f.read().strip()
    assert content.isdigit()


def test_base_install_unimplemented_raises():
    """BaseInstall.install_linux is abstract (raises NotImplementedError) for
    classes that don't override it -- exercise the "unsupported platform"
    plumbing without needing real install infra."""
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server-install")
    with pytest.raises(NotImplementedError):
        server.install_linux()


def test_server_parser_cli_help(tmp_path, monkeypatch):
    """The Typer app built by server_parser() should expose a working --help,
    exercised via Typer's CliRunner instead of a real subprocess/server."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from typer.testing import CliRunner

    from funserver.servers.base import BaseCommandServer, server_parser

    app = server_parser(BaseCommandServer("smoke-test-server"))
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_entry_point_module_path_is_importable():
    """farfarfun/todo-list#157: pyproject.toml's [project.scripts] entry used
    to point at `funserver.base:funserver`, but no `funserver/base.py` module
    ever existed -- the real function lives at
    `funserver.servers.base.base:funserver`. Fixed by pointing the console
    script entry at the real module path. `funserver.base` itself still
    doesn't exist (it was never meant to); the actual entry point target must
    resolve.
    """
    result = subprocess.run(
        [sys.executable, "-c", "from funserver.base import funserver"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "funserver.base is not expected to exist"

    result = subprocess.run(
        [sys.executable, "-c", "from funserver.servers.base.base import funserver"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_cli_installed_console_script_runs():
    """The installed `funserver` console script (from [project.scripts])
    should actually resolve and run, not just the underlying function."""
    result = subprocess.run(
        ["funserver", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "Usage" in result.stdout
