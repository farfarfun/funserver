from abc import ABC
from typing import Any

from farlog import getLogger

logger = getLogger("funserver")


class BaseStart(ABC):
    """定义服务前台运行和生命周期接口。"""

    def run_cmd(self, *args: Any, **kwargs: Any) -> str | None:
        """返回服务启动命令；没有命令时返回 None。"""
        raise NotImplementedError()

    def run(self, *args: Any, **kwargs: Any) -> None:
        """前台运行服务。"""
        raise NotImplementedError()

    def start(self, *args: Any, **kwargs: Any) -> None:
        """后台启动服务。"""
        raise NotImplementedError()

    def stop(self, *args: Any, **kwargs: Any) -> None:
        """停止服务。"""
        raise NotImplementedError()

    def update(self, *args: Any, **kwargs: Any) -> None:
        """更新服务安装内容。"""
        raise NotImplementedError()
