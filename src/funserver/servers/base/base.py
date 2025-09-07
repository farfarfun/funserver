import os
import signal

import psutil
import typer
from funbuild.shell import run_shell
from funutil import getLogger

from .start import BaseStart
from .install import BaseInstall

logger = getLogger("funserver")


class BaseServer(BaseStart, BaseInstall):
    def __init__(self, server_name):
        self.server_name = server_name
        self.dir_path = os.path.expanduser(f"~/.cache/servers/{server_name}")
        self.pid_path = f"{self.dir_path}/run.pid"
        os.makedirs(self.dir_path, exist_ok=True)
        os.makedirs(f"{self.dir_path}/logs", exist_ok=True)

    def _save_pid(self, pid_path: str = None, *args, **kwargs):
        pid_path = pid_path or self.pid_path
        self.__write_pid(pid_path)

    def _run(self, *args, **kwargs):
        self.__write_pid()
        cmd = self.run_cmd(*args, **kwargs)
        if cmd is not None:
            run_shell(cmd)
        else:
            self.run(*args, **kwargs)

    def _start(self, *args, **kwargs):
        cmd2 = self.run_cmd(*args, **kwargs)
        if cmd2 is None:
            cmd2 = f"{self.server_name} run "
        logger.success(f"started server with command: {cmd2}")
        cmd = f"nohup {cmd2} >> {self.dir_path}/logs/run-$(date +%Y-%m-%d).log 2>&1 & "
        run_shell(cmd)
        logger.success(f"{self.server_name} start success")

    def _stop(self, *args, **kwargs):
        self.__kill_pid()
        self.stop(*args, **kwargs)

    def _restart(self, *args, **kwargs):
        self._stop(*args, **kwargs)
        self._start(*args, **kwargs)

    def _update(self, *args, **kwargs):
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


def server_parser(server: BaseServer):
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
    def start(self, *args, **kwargs):
        logger.success("start")

    def stop(self, *args, **kwargs):
        logger.success("end")


def funserver():
    app = server_parser(BaseCommandServer("funserver"))
    app()
