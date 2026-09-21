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
# 启动开发环境（后台）
scripts/setup.sh start dev

# 停止服务器
scripts/setup.sh stop dev

# 重启服务器
scripts/setup.sh restart dev

# 更新服务器
funserver update

# 运行服务器（前台运行）
scripts/setup.sh run dev

# 查看开发环境状态
scripts/setup.sh status
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
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
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

## 服务生命周期

`scripts/setup.sh` 必须从仓库根目录以外的位置也能运行：

```bash
scripts/setup.sh start dev   # 后台运行
scripts/setup.sh run dev     # 前台运行
scripts/setup.sh stop dev
scripts/setup.sh restart dev
scripts/setup.sh status
```

生产环境要求当前环境已安装 `funserver` 命令：

```bash
scripts/setup.sh start prod
```

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
