import argparse
import os
import signal

import psutil
from funbuild.shell import run_shell


class BaseServer:
    def __init__(self, server_name):
        self.server_name = server_name
        self.dir_path = os.path.expanduser(f"~/.cache/servers/{server_name}")
        self.pid_path = f"{self.dir_path}/run.pid"
        os.makedirs(self.dir_path, exist_ok=True)
        os.makedirs(f"{self.dir_path}/logs", exist_ok=True)

    def run_cmd(self, *args, **kwargs) -> str:
        return None

    def run(self, *args, **kwargs):
        pass

    def stop(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def _save_pid(self, pid_path=None, *args, **kwargs):
        pid_path = pid_path or self.pid_path
        self.__write_pid(pid_path)

    def _run(self, *args, **kwargs):
        self.__write_pid()
        cmd = self.run_cmd(*args, **kwargs)
        if cmd is not None:
            run_shell([cmd])
        else:
            self.run(*args, **kwargs)

    def _start(self, *args, **kwargs):
        cmd2 = self.run_cmd(*args, **kwargs)
        if cmd2 is None:
            cmd2 = f"{self.server_name} run "
        cmd = f"nohup {cmd2} >> {self.dir_path}/logs/run-$(date +%Y-%m-%d).log 2>&1 & "
        run_shell(cmd)
        print(f"{self.server_name} start success")

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
            print(f"{cache_dir} not exists.make dir")
            os.makedirs(cache_dir)
        with open(pid_path, "w") as f:
            print(f"current pid={os.getpid()},write to {pid_path}")
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
            print(f"pid {pid} not exists")
            return
        p = psutil.Process(pid)
        print(pid, p.cwd(), p.name(), p.username(), p.cmdline())
        os.kill(pid, signal.SIGKILL)


def server_parser(server: BaseServer):
    parser = argparse.ArgumentParser(prog="PROG")
    subparsers = parser.add_subparsers(help="sub-command help")

    build_parser1 = subparsers.add_parser("pid", help="save current pid")
    build_parser1.add_argument("--pid_path", default=None, help="pid_path")
    build_parser1.set_defaults(func=server._save_pid)

    build_parser1 = subparsers.add_parser("run", help="run server")
    build_parser1.set_defaults(func=server._run)

    build_parser1 = subparsers.add_parser("start", help="start server")
    build_parser1.set_defaults(func=server._start)

    build_parser3 = subparsers.add_parser("stop", help="stop server")
    build_parser3.set_defaults(func=server._stop)

    build_parser2 = subparsers.add_parser("restart", help="restart server")
    build_parser2.set_defaults(func=server._restart)

    build_parser4 = subparsers.add_parser("update", help="update server")
    build_parser4.set_defaults(func=server._update)
    return parser, subparsers


class BaseCommandServer(BaseServer):
    def start(self, *args, **kwargs):
        print("start")

    def stop(self, *args, **kwargs):
        print("end")


def funserver():
    server = BaseCommandServer("funserver")
    parser = server_parser(server)
    args = parser.parse_args()
    params = vars(args)
    args.func(**params)
