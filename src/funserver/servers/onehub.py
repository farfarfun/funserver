import os
from typing import Optional

import requests
from funbuild.shell import run_shell_list
from funutil import getLogger

from funserver.servers.base.base import BaseServer, server_parser

logger = getLogger("fun-onehub")


class FunOneHub(BaseServer):
    def __init__(self, overwrite: bool = False, *args, **kwargs):
        super().__init__(server_name="funonehub")
        self.overwrite = overwrite

    def update(self, args=None, **kwargs):
        run_shell_list(["pip install -U funserver"])

    def run_cmd(self, *args, **kwargs) -> Optional[str]:
        root = f"{os.environ['HOME']}/opt/one-hub"
        if not os.path.exists(root):
            logger.warning(f"{root} not exists")
            return None
        if not os.path.exists(f"{root}/config.yaml"):
            logger.warning(f"{root}/config.yaml not exists")
            return None
        return f"{root}/one-api --config {root}/config.yaml"

    def get_download_url(self) -> dict[str, str]:
        url = "https://api.github.com/repos/MartialBE/one-hub/releases/latest"
        response = requests.get(url).json()
        return dict(
            (asset["name"], asset["browser_download_url"])
            for asset in response["assets"]
        )

    def _install(self, device="one-api", *args, **kwargs) -> bool:
        root = f"{os.environ.get('HOME')}/opt/one-hub"
        if not os.path.exists(root):
            logger.info(f"目录{root}不存在，创建")
            os.makedirs(root, exist_ok=True)

        run_shell_list(
            [
                f"cd {root}",
                f"curl -L -o one-api {self.get_download_url()[device]}",
                "chmod u+x one-api",
            ]
        )
        return True

    def install_linux(self, *args, **kwargs) -> bool:
        return self._install("one-api", *args, **kwargs)

    def install_macos(self, *args, **kwargs) -> bool:
        return self._install("one-api-macos", *args, **kwargs)

    def install_windows(self, *args, **kwargs) -> bool:
        return self._install("one-api.exe", *args, **kwargs)


def funonehub():
    app = server_parser(FunOneHub())
    app()
