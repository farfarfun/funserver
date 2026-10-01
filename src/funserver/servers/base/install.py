import sys
from abc import ABC
from typing import Any

from farlog import getLogger

logger = getLogger("funserver")


class BaseInstall(ABC):
    """定义跨平台安装和卸载接口。"""

    def install(self, *args: Any, **kwargs: Any) -> bool:
        """按当前操作系统安装服务并返回是否成功。"""
        if sys.platform.startswith("linux"):
            logger.info("当前系统为 Linux")
            return self.install_linux(*args, **kwargs)
        elif sys.platform.startswith("darwin"):
            logger.info("当前系统为 macOS")
            return self.install_macos(*args, **kwargs)
        elif sys.platform.startswith("win"):
            logger.info("当前系统为 Windows")
            return self.install_windows(*args, **kwargs)
        else:
            logger.error("无法识别当前系统")
            return False

    def uninstall(self, *args: Any, **kwargs: Any) -> bool:
        """按当前操作系统卸载服务并返回是否成功。"""
        if sys.platform.startswith("linux"):
            logger.info("当前系统为 Linux")
            return self.uninstall_linux(*args, **kwargs)
        elif sys.platform.startswith("darwin"):
            logger.info("当前系统为 macOS")
            return self.uninstall_macos(*args, **kwargs)
        elif sys.platform.startswith("win"):
            logger.info("当前系统为 Windows")
            return self.uninstall_windows(*args, **kwargs)
        else:
            logger.error("无法识别当前系统")
            return False

    def install_linux(self, *args: Any, **kwargs: Any) -> bool:
        """在 Linux 上安装服务。"""
        raise NotImplementedError()

    def install_macos(self, *args: Any, **kwargs: Any) -> bool:
        """在 macOS 上安装服务，默认复用 Linux 实现。"""
        return self.install_linux(*args, **kwargs)

    def install_windows(self, *args: Any, **kwargs: Any) -> bool:
        """在 Windows 上安装服务。"""
        raise NotImplementedError()

    def uninstall_linux(self, *args: Any, **kwargs: Any) -> bool:
        """在 Linux 上卸载服务。"""
        raise NotImplementedError()

    def uninstall_macos(self, *args: Any, **kwargs: Any) -> bool:
        """在 macOS 上卸载服务，默认复用 Linux 实现。"""
        return self.install_linux(*args, **kwargs)

    def uninstall_windows(self, *args: Any, **kwargs: Any) -> bool:
        """在 Windows 上卸载服务。"""
        raise NotImplementedError()
