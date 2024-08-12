import os.path

from funserver.base import BaseServer, server_parser
from pyintime.build.shell import run_shell_list


class FunJupyter(BaseServer):
    def __init__(self):
        super().__init__(server_name="funjupyter")

    def update(self, args=None, **kwargs):
        run_shell_list(["pip install -U jupyterlab"])

    def run_cmd(self, *args, **kwargs):
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.py"
        )
        return f"jupyter lab --config {config_path} --watch "


def funjupyter():
    server = FunJupyter()
    parser = server_parser(server)
    args = parser.parse_args()
    params = vars(args)
    args.func(**params)
