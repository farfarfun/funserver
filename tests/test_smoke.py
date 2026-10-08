"""funserver 公共 API 的轻量测试。

测试使用临时 HOME，避免绑定真实端口、启动真实服务或修改用户目录。
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest


def test_import_top_level():
    """顶层包名应与仓库名和 PyPI 包名一致并可导入。"""
    import funserver  # noqa: F401


def test_import_servers_subpackage():
    """服务器子包本身应可正常导入。

    `funserver.servers` 不重新导出基础类，公共导入路径是
    `funserver.servers.base`。
    """
    import funserver.servers  # noqa: F401


def test_import_public_classes():
    """基础模块应导出公开类和命令行解析器。"""
    from funserver.servers.base import BaseCommandServer, BaseServer, server_parser

    assert BaseServer is not None
    assert BaseCommandServer is not None
    assert callable(server_parser)


def test_base_command_server_construct(tmp_path, monkeypatch):
    """构造基础命令服务时应在隔离的 HOME 下创建缓存目录。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")

    assert server.server_name == "smoke-test-server"
    assert server.port == -1
    assert str(tmp_path) in server.dir_path
    # 初始化过程应在隔离目录中创建缓存和日志目录。
    import os

    assert os.path.isdir(server.dir_path)
    assert os.path.isdir(f"{server.dir_path}/logs")
    assert server.run_path == f"{tmp_path}/opt/smoke-test-server"


def test_base_command_server_start_stop(tmp_path, monkeypatch):
    """基础命令服务的启动和停止操作应可直接调用。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")
    # 空操作实现不应抛出异常。
    server.start()
    server.stop()


def test_base_command_server_run_does_not_raise(tmp_path, monkeypatch):
    """CLI 默认的空操作服务执行 `_run()`（即 `funserver run`）不应抛出异常。

    回归测试：此前 `BaseCommandServer` 只覆盖了 `start`/`stop`，未覆盖
    `run`/`run_cmd`，导致 `_run()` 必定命中 `BaseStart.run_cmd` 的
    `NotImplementedError`，已安装的 `funserver run` 命令每次都会崩溃。
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")
    server._run()
    assert not os.path.exists(server.pid_path)


def test_base_command_server_save_pid(tmp_path, monkeypatch):
    """保存 PID 时应写入隔离 HOME 下的文件。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server")
    server._save_pid()

    with open(server.pid_path) as f:
        content = f.read().strip()
    assert content.isdigit()


def test_base_server_run_command_executes_without_writing_managed_pid(tmp_path, monkeypatch):
    """前台命令不应将 CLI 自身写成可由 stop 管理的服务 PID。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    import funserver.servers.base.base as base_mod
    from funserver.servers.base import BaseServer

    class CommandServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "echo ok"

    server = CommandServer("command-server")
    with pytest.MonkeyPatch.context() as patcher:
        calls = []
        patcher.setattr(base_mod, "run_shell", lambda command: calls.append(command) or "0")
        server._run()

    assert calls == ["echo ok"]
    assert not os.path.exists(server.pid_path)


def test_start_rejects_live_managed_process(tmp_path, monkeypatch):
    """重复 start 不得覆盖仍然指向受管进程的 PID 文件。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseServer

    class SleepServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "sleep 30"

    server = SleepServer("duplicate-start-server")
    server._start()
    try:
        with pytest.raises(RuntimeError, match="already running"):
            server._start()
    finally:
        server._stop()


def test_start_creates_missing_run_path(tmp_path, monkeypatch):
    """后台启动应自行创建文档约定的运行目录。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseServer

    class SleepServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "sleep 30"

    server = SleepServer("create-run-path-server")
    assert not os.path.exists(server.run_path)
    server._start()
    try:
        assert os.path.isdir(server.run_path)
    finally:
        server._stop()


def test_start_refuses_live_pid_without_signature(tmp_path, monkeypatch):
    """活跃 PID 缺少身份签名时不得被当作陈旧记录覆盖。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseServer

    class CommandServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "echo should-not-run"

    server = CommandServer("unverified-pid-server")
    with open(server.pid_path, "w") as f:
        f.write(str(os.getpid()))

    with pytest.raises(RuntimeError, match="cannot verify existing pid"):
        server._start()
    assert os.path.exists(server.pid_path)


def test_run_command_failure_raises(tmp_path, monkeypatch):
    """外部命令失败必须使生命周期命令失败。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    import funserver.servers.base.base as base_mod
    from funserver.servers.base import BaseServer

    class CommandServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "false"

    server = CommandServer("failed-command-server")
    monkeypatch.setattr(base_mod, "run_shell", lambda command: "1")
    with pytest.raises(RuntimeError, match="command failed"):
        server._run()


def test_start_then_stop_terminates_managed_process(tmp_path, monkeypatch):
    """`_start` 应记录真实后台子进程的 PID；`_stop` 应能据此定位并终止该进程。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from funserver.servers.base import BaseServer

    class SleepServer(BaseServer):
        def run_cmd(self, *args: object, **kwargs: object) -> str:
            return "sleep 30"

        def stop(self, *args: object, **kwargs: object) -> None:
            """跳过默认的按端口/进程名兜底清理，只验证基于 PID 签名的终止逻辑。"""

    server = SleepServer("sleep-server")
    os.makedirs(server.run_path, exist_ok=True)

    server._start()
    try:
        assert os.path.exists(server.pid_path)
        with open(server.pid_path) as f:
            pid = int(f.read().strip())
        assert psutil.pid_exists(pid)
        # fork 之后到 execve 替换进程镜像之间有极短窗口，这段时间里 `comm`
        # 可能还显示父 shell 的名字，短暂轮询等它稳定成目标命令名。
        name = ""
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                name = psutil.Process(pid).name()
            except psutil.NoSuchProcess:
                break
            if "sleep" in name:
                break
            time.sleep(0.02)
        assert "sleep" in name
        assert os.path.exists(f"{server.pid_path}.meta")

        server._stop()

        deadline = time.monotonic() + 5
        while psutil.pid_exists(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not psutil.pid_exists(pid)
    finally:
        if psutil.pid_exists(pid):
            psutil.Process(pid).kill()

    assert not os.path.exists(server.pid_path)
    assert not os.path.exists(f"{server.pid_path}.meta")


def test_stop_with_mismatched_pid_signature_does_not_kill(tmp_path, monkeypatch):
    """PID 文件记录的启动时间与实际进程不符时，必须判定为陈旧 PID，不发送终止信号。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    import signal

    import funserver.servers.base.base as base_mod
    from funserver.servers.base import BaseServer

    class NoOpStopServer(BaseServer):
        def stop(self, *args: object, **kwargs: object) -> None:
            """同上，隔离默认兜底清理。"""

    server = NoOpStopServer("mismatch-server")
    # 用当前测试进程的真实 PID 伪造一份 PID 文件，但签名写一个明显错误的启动时间，
    # 模拟「PID 被操作系统回收后分配给无关进程」的场景。
    with open(server.pid_path, "w") as f:
        f.write(str(os.getpid()))
    with open(f"{server.pid_path}.meta", "w") as f:
        f.write("1.0")

    real_kill = base_mod.os.kill
    killed = []

    def fake_kill(pid, sig):
        # `psutil.pid_exists` 内部也会用 0 号信号探测进程是否存在，
        # 这里只拦截真正的终止信号（SIGKILL/SIGTERM），探测调用原样放行。
        if sig in (signal.SIGKILL, signal.SIGTERM):
            killed.append((pid, sig))
            return
        return real_kill(pid, sig)

    monkeypatch.setattr(base_mod.os, "kill", fake_kill)

    server._stop()

    assert killed == []
    assert not os.path.exists(server.pid_path)


def test_stop_without_pid_file_is_noop(tmp_path, monkeypatch):
    """没有 PID 文件时（从未启动或已清理），`_stop` 不应尝试终止任何进程。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    import funserver.servers.base.base as base_mod
    from funserver.servers.base import BaseServer

    class NoOpStopServer(BaseServer):
        def stop(self, *args: object, **kwargs: object) -> None:
            """同上，隔离默认兜底清理。"""

    server = NoOpStopServer("empty-server")
    killed = []
    monkeypatch.setattr(base_mod.os, "kill", lambda pid, sig: killed.append((pid, sig)))

    server._stop()

    assert killed == []


def test_cli_install_nonzero_exit_on_failure(tmp_path, monkeypatch):
    """`install` 返回 False 时，CLI 必须以非 0 退出码结束，不能静默成功退出。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from typer.testing import CliRunner

    from funserver.servers.base import BaseCommandServer, server_parser

    server = BaseCommandServer("install-fail-server")
    monkeypatch.setattr(server, "install", lambda *a, **kw: False)
    app = server_parser(server)
    result = CliRunner().invoke(app, ["install"])

    assert result.exit_code != 0


def test_cli_install_zero_exit_on_success(tmp_path, monkeypatch):
    """`install` 返回 True 时，CLI 应以 0 退出码正常结束。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from typer.testing import CliRunner

    from funserver.servers.base import BaseCommandServer, server_parser

    server = BaseCommandServer("install-ok-server")
    monkeypatch.setattr(server, "install", lambda *a, **kw: True)
    app = server_parser(server)
    result = CliRunner().invoke(app, ["install"])

    assert result.exit_code == 0


def test_base_install_unimplemented_raises():
    """未实现的平台安装方法应抛出 NotImplementedError。"""
    from funserver.servers.base import BaseCommandServer

    server = BaseCommandServer("smoke-test-server-install")
    with pytest.raises(NotImplementedError):
        server.install_linux()


@pytest.mark.parametrize(
    ("platform", "method_name"),
    [
        ("linux", "install_linux"),
        ("darwin", "install_macos"),
        ("win32", "install_windows"),
    ],
)
def test_base_install_dispatches_platform(platform, method_name, monkeypatch):
    """安装入口应按平台分发，并完整透传位置参数和关键字参数。"""
    from funserver.servers.base.install import BaseInstall

    calls = []
    installer = BaseInstall()
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setattr(
        installer,
        method_name,
        lambda *args, **kwargs: calls.append((args, kwargs)) or True,
    )

    assert installer.install("value", enabled=True) is True
    assert calls == [(("value",), {"enabled": True})]


def test_server_parser_cli_help(tmp_path, monkeypatch):
    """命令行解析器应生成可正常显示帮助信息的应用。"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from typer.testing import CliRunner

    from funserver.servers.base import BaseCommandServer, server_parser

    app = server_parser(BaseCommandServer("smoke-test-server"))
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_entry_point_module_path_is_importable():
    """命令行入口应指向实际存在且可导入的模块。"""
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
    """已安装的 funserver 命令应能解析入口并显示帮助信息。"""
    result = subprocess.run(["funserver", "--help"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Usage" in result.stdout


def test_cli_installed_console_script_run_exits_cleanly(tmp_path):
    """已安装的 `funserver run` 命令应正常退出，不应抛出未处理异常。

    回归测试：修复前 `BaseCommandServer` 未覆盖 `run`/`run_cmd`，`funserver run`
    每次都会因 `NotImplementedError` 崩溃（非 0 退出码并打印异常堆栈）。
    """
    env = os.environ | {"HOME": str(tmp_path)}
    result = subprocess.run(["funserver", "run"], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    assert "NotImplementedError" not in result.stderr


def test_lifecycle_script_contract():
    script = Path(__file__).parents[1] / "scripts" / "setup.sh"
    assert script.is_file()
    result = subprocess.run(["bash", str(script), "status"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "dev:" in result.stdout and "prod:" in result.stdout


def test_lifecycle_script_process_identity(tmp_path):
    """脚本应拒绝重复启动，并且不得终止与 PID 记录不匹配的进程。"""
    project_dir = tmp_path / "project"
    scripts_dir = project_dir / "scripts"
    bin_dir = tmp_path / "bin"
    scripts_dir.mkdir(parents=True)
    bin_dir.mkdir()
    source_script = Path(__file__).parents[1] / "scripts" / "setup.sh"
    script = scripts_dir / "setup.sh"
    shutil.copy2(source_script, script)
    fake_uv = bin_dir / "uv"
    fake_uv.write_text("#!/usr/bin/env bash\nwhile :; do sleep 1; done\n")
    fake_uv.chmod(0o755)
    env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}"}

    started = subprocess.run(
        ["bash", str(script), "start", "dev"], env=env, capture_output=True, text=True
    )
    assert started.returncode == 0, started.stderr

    duplicate = subprocess.run(
        ["bash", str(script), "start", "dev"], env=env, capture_output=True, text=True
    )
    assert duplicate.returncode != 0

    stopped = subprocess.run(
        ["bash", str(script), "stop", "dev"], env=env, capture_output=True, text=True
    )
    assert stopped.returncode == 0, stopped.stderr

    pid_file = project_dir / ".run" / "funserver-dev.pid"
    pid_file.write_text(f"{os.getpid()}\n伪造启动时间\n伪造可执行文件\n伪造参数\n")
    mismatched = subprocess.run(
        ["bash", str(script), "stop", "dev"], env=env, capture_output=True, text=True
    )
    assert mismatched.returncode != 0
    assert "未发送终止信号" in mismatched.stderr
    assert os.getpid() > 0
