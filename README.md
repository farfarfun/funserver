# FunServer

[![PyPI version](https://badge.fury.io/py/funserver.svg)](https://badge.fury.io/py/funserver)
[![Python](https://img.shields.io/pypi/pyversions/funserver.svg)](https://pypi.org/project/funserver/)
[![License](https://img.shields.io/github/license/farfarfun/funserver.svg)](https://github.com/farfarfun/funserver/blob/main/LICENSE)

FunServer 是一个 Python 服务器管理框架，提供统一的接口来管理各种服务器应用程序。它支持跨平台安装、进程管理、日志记录和配置管理。

## 特性

- 🚀 **统一的服务器管理接口** - 提供 start、stop、restart、update 等标准操作
- 🔧 **跨平台支持** - 支持 Linux、macOS 和 Windows 系统
- 📊 **进程管理** - 自动 PID 跟踪和进程生命周期管理
- 📝 **日志管理** - 自动日志记录和日志文件管理
- 🎯 **模块化架构** - 易于扩展和添加新的服务器实现
- 💻 **命令行界面** - 基于 Typer 的友好命令行工具

## 安装

```bash
pip install funserver
```

## 快速开始

### 基本用法

FunServer 提供了统一的命令行接口来管理服务器：

```bash
# 启动服务器
funserver start

# 停止服务器
funserver stop

# 重启服务器
funserver restart

# 更新服务器
funserver update

# 运行服务器（前台运行）
funserver run
```

### OneHub 服务器管理

FunServer 内置了对 OneHub（API 网关）的支持：

```bash
# 安装 OneHub
funonehub install

# 启动 OneHub 服务
funonehub start

# 停止 OneHub 服务
funonehub stop

# 重启 OneHub 服务
funonehub restart

# 更新 OneHub
funonehub update
```

## 架构设计

### 核心组件

1. **BaseServer** - 服务器基类，提供标准的服务器管理功能
2. **BaseInstall** - 安装管理基类，支持跨平台安装
3. **BaseStart** - 启动管理基类，定义服务器启动接口

### 目录结构

```
src/funserver/
├── servers/
│   ├── base/           # 基础框架
│   │   ├── base.py     # 服务器基类
│   │   ├── install.py  # 安装管理
│   │   └── start.py    # 启动管理
│   ├── funjupyter/     # Jupyter 服务器支持
│   └── onehub.py       # OneHub 服务器实现
└── __init__.py
```

## 开发自定义服务器

### 创建自定义服务器

继承 `BaseServer` 类来创建自定义服务器：

```python
from funserver.servers.base.base import BaseServer, server_parser

class MyCustomServer(BaseServer):
    def __init__(self):
        super().__init__(server_name="mycustomserver")
    
    def run_cmd(self, *args, **kwargs):
        # 返回启动服务器的命令
        return "my-server --config config.yaml"
    
    def install_linux(self, *args, **kwargs):
        # Linux 安装逻辑
        return True
    
    def install_macos(self, *args, **kwargs):
        # macOS 安装逻辑
        return True
    
    def install_windows(self, *args, **kwargs):
        # Windows 安装逻辑
        return True
    
    def update(self, *args, **kwargs):
        # 更新逻辑
        pass

def mycustomserver():
    app = server_parser(MyCustomServer())
    app()
```

### 注册命令行工具

在 `pyproject.toml` 中添加脚本入口：

```toml
[project.scripts]
mycustomserver = "mypackage.servers.custom:mycustomserver"
```

## API 参考

### BaseServer

主要方法：

- `start()` - 启动服务器（后台运行）
- `stop()` - 停止服务器
- `restart()` - 重启服务器
- `run()` - 运行服务器（前台运行）
- `update()` - 更新服务器
- `install()` - 安装服务器
- `run_cmd()` - 返回启动命令（需要子类实现）

### 配置

服务器配置和日志文件默认存储在：
- 配置目录：`~/.cache/servers/{server_name}/`
- 日志目录：`~/.cache/servers/{server_name}/logs/`
- PID 文件：`~/.cache/servers/{server_name}/run.pid`

## 依赖项

- `click>=8.1.8` - 命令行界面
- `funbuild>=1.5.11` - 构建工具
- `funutil>=1.0.50` - 实用工具
- `psutil>=7.0.0` - 进程管理
- `typer>=0.15.3` - 现代命令行界面

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 作者

- **牛哥** - *初始工作* - [niuliangtao@qq.com](mailto:niuliangtao@qq.com)
- **farfarfun** - *维护者* - [farfarfun@qq.com](mailto:farfarfun@qq.com)

## 链接

- [GitHub 组织](https://github.com/farfarfun)
- [项目仓库](https://github.com/farfarfun/funserver)
- [发布页面](https://github.com/farfarfun/funserver/releases)

## 更新日志

### v1.0.52
- 当前版本
- 支持 OneHub 服务器管理
- 完善的跨平台安装支持
- 改进的日志管理系统