# 更新日志

## [未发布]

### 修复

- `BaseServer.__kill_pid` 补充进程身份校验（启动时间签名），PID 被系统回收后
  分配给无关进程时不再误发 `SIGKILL`；不匹配时只清理陈旧 PID/签名文件。
- 修复 `__kill_pid` 原先用多个位置参数调用 `logger.success(pid, ...)` 导致
  只要命中存活 PID 就必定抛 `AttributeError` 的 bug（farlog 的 `.success()`
  首参须是消息字符串），该路径此前从未真正执行到 `os.kill`。
- `_start` 补写真实后台子进程 PID 及身份签名（此前只有 `_run` 前台路径写
  PID，后台启动的进程从未被正确记录，`stop`/`restart` 对其无法基于 PID 定位）。
- 修复 `BaseCommandServer`（已安装的 `funserver` CLI 默认实现）未覆盖
  `run`/`run_cmd`，导致 `funserver run` 必定抛 `NotImplementedError` 崩溃的
  问题；其 `start()` 覆盖此前也是死代码（CLI 实际调用的是 `_start()`）。
- Typer 的 `install`/`uninstall` 命令现在在返回 `False` 时以非 0 退出码结束，
  不再静默返回成功。
- `scripts/setup.sh` 启动时固定 `cd` 到脚本自身所在的项目根目录，修复从仓库
  外的工作目录调用时 `uv run` 可能找不到本项目或解析到错误项目的问题。
- `__kill_pid`/`_start` 的日志不再记录完整命令行、`cwd`、用户名等可能包含
  凭据的信息，只记录服务名和 PID。

### 变更

- README 区分"仅安装 PyPI 包"与"克隆仓库使用 `scripts/setup.sh`"两种场景的
  示例，避免用户照着文档执行一个包安装不会带来的脚本。

### 新增

- 引入 `ruff` 作为 lint/format 工具（dev 依赖 + `[tool.ruff]` 配置），并修复
  既有的导入顺序/未使用导入问题。
- 补充覆盖 PID 身份校验、后台启动真实子进程、CLI 失败退出码的测试。

## [1.0.72] - 2026-09-21

### 新增

- 增加 `scripts/setup.sh` 生命周期入口，支持开发/生产环境和状态查询。

### 修复

- 补齐项目的 MIT 元数据、运行时目录忽略规则和规范文档。

### 变更

- README 仅保留当前实际提供的 `funserver` CLI 和基础服务组件。

### 废弃

- 移除 README 中不存在的 OneHub/Jupyter 示例。
