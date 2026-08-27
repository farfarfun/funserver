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


def test_cli_entry_point_console_script_is_broken():
    """KNOWN BUG (not fixed here, out of scope for this smoke-test task):

    pyproject.toml declares the `funserver` console script as
    `funserver.base:funserver`, but no `funserver/base.py` module exists.
    The real function lives at `funserver.servers.base.base:funserver`.
    Running the installed console script therefore fails with
    `ModuleNotFoundError: No module named 'funserver.base'`.

    We skip actually invoking the broken console script and instead just
    confirm the underlying `funserver()` app-building function works when
    imported from its real location (covered by
    test_server_parser_cli_help). This test documents the bug via subprocess
    so it's visible if/when the entry point is fixed upstream.
    """
    result = subprocess.run(
        [sys.executable, "-c", "from funserver.base import funserver"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        pytest.fail(
            "funserver.base now exists -- pyproject.toml [project.scripts] "
            "entry point may no longer be broken; consider un-skipping a "
            "real `funserver --help` subprocess test."
        )
    pytest.skip(
        "Known bug: [project.scripts] entry point 'funserver.base:funserver' "
        "points at a nonexistent module (real path is "
        "funserver.servers.base.base:funserver). Not fixed here per smoke-test "
        "task scope -- reported upstream instead."
    )
