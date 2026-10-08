import os
import signal
from typing import Any

import psutil
import typer
from farlog import getLogger
from funshell import kill_process, run_shell

from .install import BaseInstall
from .start import BaseStart

logger = getLogger("funserver")


class BaseServer(BaseStart, BaseInstall):
    """提供服务目录、PID 文件和生命周期操作的基础实现。"""

    def __init__(self, server_name: str, port: int = -1, *args: Any, **kwargs: Any) -> None:
        """初始化服务名称和默认缓存目录。"""
        self.port = port
        self.server_name = server_name
        self.dir_path = os.path.expanduser(f"~/.cache/servers/{server_name}")
        self.pid_path = f"{self.dir_path}/run.pid"
        os.makedirs(self.dir_path, exist_ok=True)
        os.makedirs(f"{self.dir_path}/logs", exist_ok=True)

    @property
    def run_path(self) -> str:
        """返回服务运行目录。"""
        return f"{os.environ['HOME']}/opt/{self.server_name}"

    def stop(self, *args: Any, **kwargs: Any) -> None:
        """停止占用服务端口或匹配服务名称的进程。"""
        kill_process(port=self.port, name=self.server_name)

    def _save_pid(self, pid_path: str | None = None, *args: Any, **kwargs: Any) -> None:
        """将当前进程 PID 写入指定文件。"""
        pid_path = pid_path or self.pid_path
        self.__write_pid(pid_path)

    def _run(self, *args: Any, **kwargs: Any) -> None:
        """前台执行服务命令。

        前台命令的子进程不一定继承 CLI 进程的 PID，因此不能将当前 CLI
        进程登记为可由 ``stop`` 管理的服务进程。
        """
        cmd = self.run_cmd(*args, **kwargs)
        if cmd is not None:
            self.__run_shell(cmd)
        else:
            self.run(*args, **kwargs)

    def _start(self, *args: Any, **kwargs: Any) -> None:
        """后台启动服务，记录真实子进程 PID 并将输出写入日期日志。"""
        if self.__is_managed_process_running():
            raise RuntimeError(f"{self.server_name} is already running")
        if os.path.exists(self.pid_path):
            pid = self.__read_pid()
            if pid > 0 and psutil.pid_exists(pid) and self.__read_signature() is None:
                raise RuntimeError(f"cannot verify existing pid for {self.server_name}")
            self.__remove_pid_files()
        os.makedirs(self.run_path, exist_ok=True)
        cmd2 = self.run_cmd(*args, **kwargs)
        if cmd2 is None:
            cmd2 = f"{self.server_name} run "
        logger.success(f"starting {self.server_name} in background")
        log_path = f"{self.dir_path}/logs/run-$(date +%Y-%m-%d).log"
        # 用子 shell 包住 nohup，让 `$!` 取到的是实际后台进程的 PID，
        # 而不是 `cd && nohup ...` 整个复合命令被放入后台后的包装进程 PID。
        cmd = (
            f'cd "{self.run_path}" && '
            f'(nohup {cmd2} >>"{log_path}" 2>&1 & echo $! >"{self.pid_path}")'
        )
        self.__run_shell(cmd)
        self.__write_signature_from_pid_file()
        if not self.__is_managed_process_running():
            self.__remove_pid_files()
            raise RuntimeError(f"{self.server_name} failed to start")
        logger.success(f"{self.server_name} start success")

    def _stop(self, *args: Any, **kwargs: Any) -> None:
        """清理 PID 文件并停止服务进程。"""
        self.__kill_pid()
        self.stop(*args, **kwargs)

    def _restart(self, *args: Any, **kwargs: Any) -> None:
        """停止后重新启动服务。"""
        self._stop(*args, **kwargs)
        self._start(*args, **kwargs)

    def _update(self, *args: Any, **kwargs: Any) -> None:
        """停止服务、执行更新并重新启动。"""
        self._stop(*args, **kwargs)
        self.update(*args, **kwargs)
        self._start(*args, **kwargs)

    def __signature_path(self, pid_path: str | None = None) -> str:
        """返回与 PID 文件配套的进程身份签名文件路径。"""
        return f"{pid_path or self.pid_path}.meta"

    def __write_pid(self, pid_path=None):
        pid_path = pid_path or self.pid_path
        cache_dir = os.path.dirname(pid_path)
        if not os.path.exists(cache_dir):
            logger.success(f"{cache_dir} not exists.make dir")
            os.makedirs(cache_dir)
        pid = os.getpid()
        with open(pid_path, "w") as f:
            logger.success(f"current pid={pid},write to {pid_path}")
            f.write(str(pid))
        self.__write_signature(pid, pid_path)

    def __run_shell(self, command: str) -> None:
        """运行命令，并将 shell 失败转换为生命周期失败。"""
        result = run_shell(command)
        if result != "0":
            raise RuntimeError(f"{self.server_name} command failed: {result}")

    def __write_signature_from_pid_file(self, pid_path: str | None = None) -> None:
        """`_start` 用子 shell 写完 PID 文件后，补写对应的进程身份签名。"""
        pid = self.__read_pid(pid_path=pid_path)
        if pid > 0:
            self.__write_signature(pid, pid_path)

    def __write_signature(self, pid: int, pid_path: str | None = None) -> None:
        try:
            create_time = psutil.Process(pid).create_time()
        except psutil.Error:
            logger.warning(f"pid {pid} 启动后立即读取进程信息失败，跳过身份签名记录")
            return
        with open(self.__signature_path(pid_path), "w") as f:
            f.write(repr(create_time))

    def __read_pid(self, remove=False, pid_path: str | None = None):
        pid_path = pid_path or self.pid_path
        pid = -1
        if os.path.exists(pid_path):
            with open(pid_path, "r") as f:
                content = f.read().strip()
            if content:
                try:
                    pid = int(content)
                except ValueError:
                    pid = -1
            if remove:
                os.remove(pid_path)
        return pid

    def __read_signature(self, remove=False, pid_path: str | None = None) -> float | None:
        path = self.__signature_path(pid_path)
        create_time: float | None = None
        if os.path.exists(path):
            with open(path, "r") as f:
                content = f.read().strip()
            if content:
                try:
                    create_time = float(content)
                except ValueError:
                    create_time = None
            if remove:
                os.remove(path)
        return create_time

    def __remove_pid_files(self, pid_path: str | None = None) -> None:
        """删除一对已确认陈旧的 PID 身份记录。"""
        path = pid_path or self.pid_path
        for file_path in (path, self.__signature_path(path)):
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass

    def __is_managed_process_running(self, pid_path: str | None = None) -> bool:
        """PID 和创建时间都匹配时，才把进程视为本服务的活跃实例。"""
        pid = self.__read_pid(pid_path=pid_path)
        expected_create_time = self.__read_signature(pid_path=pid_path)
        if pid <= 0 or expected_create_time is None or not psutil.pid_exists(pid):
            return False
        try:
            actual_create_time = psutil.Process(pid).create_time()
        except psutil.Error:
            return False
        return abs(actual_create_time - expected_create_time) <= 1

    def __kill_pid(self):
        """终止由 `_run`/`_start` 记录的服务进程。

        仅凭 PID 文件里的号码不足以确认进程仍是本服务——PID 可能被操作系统
        回收后分配给了完全无关的进程。这里额外核对进程启动时间（创建时记录的
        签名文件），身份不匹配时只清理陈旧文件并放弃发送终止信号。
        """
        pid = self.__read_pid()
        expected_create_time = self.__read_signature()
        self.__remove_pid_files()
        if pid <= 0 or not psutil.pid_exists(pid):
            logger.warning(f"pid {pid} not exists")
            return
        try:
            actual_create_time = psutil.Process(pid).create_time()
        except psutil.Error:
            logger.warning(f"pid {pid} 无法读取进程信息，判定为陈旧 PID，不发送终止信号")
            return
        if expected_create_time is None or abs(actual_create_time - expected_create_time) > 1:
            logger.warning(f"pid {pid} 的启动时间与记录不符，判定为陈旧 PID，不发送终止信号")
            return
        # 仅记录服务名与 PID，不把完整命令行/工作目录/用户名写入日志，
        # 避免启动命令中可能携带的 token、密码等敏感参数泄露到日志文件。
        logger.success(f"terminating managed process {self.server_name} (pid={pid})")
        os.kill(pid, signal.SIGKILL)


def server_parser(server: BaseServer) -> typer.Typer:
    """为服务实例创建 Typer 生命周期命令行应用。"""
    app = typer.Typer()

    @app.command()
    def pit(pid_path: str = typer.Option(default=None, help="pid_path")):
        server._save_pid(pid_path=pid_path)

    @app.command()
    def run():
        server._run()

    @app.command()
    def start():
        server._start()

    @app.command()
    def stop():
        server._stop()

    @app.command()
    def restart():
        server._restart()

    @app.command()
    def update():
        server._update()

    @app.command()
    def install():
        if not server.install():
            logger.error(f"{server.server_name} install failed")
            raise typer.Exit(code=1)

    @app.command()
    def uninstall():
        if not server.uninstall():
            logger.error(f"{server.server_name} uninstall failed")
            raise typer.Exit(code=1)

    return app


class BaseCommandServer(BaseServer):
    """用于测试和基础命令的空操作服务实现。"""

    def run_cmd(self, *args: Any, **kwargs: Any) -> str | None:
        """空操作实现没有外部命令可执行，交给 `run()` 处理。"""
        return None

    def run(self, *args: Any, **kwargs: Any) -> None:
        """记录前台运行动作。"""
        logger.success("run")

    def start(self, *args: Any, **kwargs: Any) -> None:
        """记录启动动作。"""
        logger.success("start")

    def stop(self, *args: Any, **kwargs: Any) -> None:
        """记录停止动作。"""
        logger.success("end")


def funserver() -> None:
    """启动 funserver 默认命令行应用。"""
    app = server_parser(BaseCommandServer("funserver"))
    app()
