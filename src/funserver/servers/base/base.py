import os
import signal
from typing import Any

import psutil
import typer
from funshell import run_shell, run_shell_list, kill_process
from farlog import getLogger

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
        """前台执行服务命令并记录 PID。"""
        self.__write_pid()
        cmd = self.run_cmd(*args, **kwargs)
        if cmd is not None:
            run_shell(cmd)
        else:
            self.run(*args, **kwargs)

    def _start(self, *args: Any, **kwargs: Any) -> None:
        """后台启动服务并将输出写入日期日志。"""
        cmd2 = self.run_cmd(*args, **kwargs)
        if cmd2 is None:
            cmd2 = f"{self.server_name} run "
        logger.success(f"started server with command: {cmd2}")
        cmd = f"cd {self.run_path} && nohup {cmd2} >> {self.dir_path}/logs/run-$(date +%Y-%m-%d).log 2>&1 & "
        run_shell(cmd)
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

    def __write_pid(self, pid_path=None):
        pid_path = pid_path or self.pid_path
        cache_dir = os.path.dirname(pid_path)
        if not os.path.exists(cache_dir):
            logger.success(f"{cache_dir} not exists.make dir")
            os.makedirs(cache_dir)
        with open(pid_path, "w") as f:
            logger.success(f"current pid={os.getpid()},write to {pid_path}")
            f.write(str(os.getpid()))

    def __read_pid(self, remove=False):
        pid = -1
        if os.path.exists(self.pid_path):
            with open(self.pid_path, "r") as f:
                pid = int(f.read())
            if remove:
                os.remove(self.pid_path)
        return pid

    def __kill_pid(self):
        pid = self.__read_pid(remove=True)
        if not psutil.pid_exists(pid):
            logger.warning(f"pid {pid} not exists")
            return
        p = psutil.Process(pid)
        logger.success(pid, p.cwd(), p.name(), p.username(), p.cmdline())
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
        server.install()

    @app.command()
    def uninstall():
        server.uninstall()

    return app


class BaseCommandServer(BaseServer):
    """用于测试和基础命令的空操作服务实现。"""

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
