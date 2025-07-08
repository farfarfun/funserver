import os
from typing import Optional

from funbuild.shell import run_shell_list
from funutil import getLogger

from funserver.base import BaseServer, server_parser

logger = getLogger("fun-onehub")


class FunOneHub(BaseServer):
    def __init__(self):
        super().__init__(server_name="funonehub")

    def update(self, args=None, **kwargs):
        run_shell_list(["pip install -U funrec"])

    def run_cmd(self, *args, **kwargs) -> Optional[str]:
        root = f"{os.environ['HOME']}/opt/one-hub"
        if not os.path.exists(root):
            logger.warning(f"{root} not exists")
            return None
        if not os.path.exists(f"{root}/config.yaml"):
            logger.warning(f"{root}/config.yaml not exists")
            return None
        return f"{root}/one-api --config {root}/config.yaml"


def funonehub():
    app = server_parser(FunOneHub())
    app()
