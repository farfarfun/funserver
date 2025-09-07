from abc import ABC
from typing import Optional

from funutil import getLogger

logger = getLogger("funserver")


class BaseStart(ABC):
    def run_cmd(self, *args, **kwargs) -> Optional[str]:
        raise NotImplementedError()

    def run(self, *args, **kwargs):
        raise NotImplementedError()

    def start(self, *args, **kwargs):
        raise NotImplementedError()

    def stop(self, *args, **kwargs):
        raise NotImplementedError()

    def update(self, *args, **kwargs):
        raise NotImplementedError()
