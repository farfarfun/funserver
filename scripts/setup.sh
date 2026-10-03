#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
# 固定工作目录到脚本自身所在的项目根，保证从仓库外的任意目录调用本脚本时，
# `uv run` 之类依赖 CWD 查找 pyproject.toml 的命令都能定位到正确的项目。
cd -- "$ROOT_DIR"
usage() {
  printf '用法: %s {start|stop|restart|run|status} [dev|prod]\n' "${0##*/}" >&2
}

pid_file() { printf '%s/funserver-%s.pid' "$RUN_DIR" "$1"; }
log_file() { printf '%s/funserver-%s.log' "$RUN_DIR" "$1"; }
lock_dir() { printf '%s/funserver-%s.lock' "$RUN_DIR" "$1"; }

read_pid() {
  local file
  file="$(pid_file "$1")"
  if [[ -s "$file" ]]; then
    sed -n '1p' "$file"
  fi
}

process_signature() {
  local pid="$1" started executable args
  started="$(ps -p "$pid" -o lstart= 2>/dev/null)" || return 1
  executable="$(ps -p "$pid" -o comm= 2>/dev/null)" || return 1
  args="$(ps -p "$pid" -o args= 2>/dev/null)" || return 1
  printf '%s\n%s\n%s\n' "$started" "$executable" "$args"
}

managed_pid() {
  local env pid file expected actual
  env="$1"
  file="$(pid_file "$env")"
  pid="$(read_pid "$env")"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  expected="$(sed -n '2,4p' "$file")"
  [[ -n "$expected" ]] || return 1
  actual="$(process_signature "$pid")" || return 1
  [[ "$actual" == "$expected" ]]
}

command_for() {
  case "$1" in
    dev)
      if command -v uv >/dev/null 2>&1; then
        COMMAND=("$(command -v uv)" run funserver)
      else
        command -v funserver >/dev/null 2>&1 || {
          printf '开发环境需要 uv 或已安装的 funserver 命令\n' >&2
          return 1
        }
        COMMAND=("$(command -v funserver)")
      fi
      ;;
    prod)
      command -v funserver >/dev/null 2>&1 || {
        printf '生产环境需要已安装的 funserver 命令\n' >&2
        return 1
      }
      COMMAND=("$(command -v funserver)")
      ;;
    *) usage; return 2 ;;
  esac
}

run_foreground() {
  case "$1" in
    dev)
      if command -v uv >/dev/null 2>&1; then
        exec uv run funserver run
      fi
      exec funserver run
      ;;
    prod)
      command -v funserver >/dev/null 2>&1 || {
        printf '生产环境需要已安装的 funserver 命令\n' >&2
        return 1
      }
      exec funserver run
      ;;
    *) usage; return 2 ;;
  esac
}

status_one() {
  local env pid file
  env="$1"
  file="$(pid_file "$env")"
  if managed_pid "$env"; then
    pid="$(read_pid "$env")"
    printf '%s: running (pid %s)\n' "$env" "$pid"
  elif [[ -e "$file" ]]; then
    rm -f -- "$file"
    rmdir "$(lock_dir "$env")" 2>/dev/null || true
    printf '%s: stale pid removed\n' "$env"
  else
    rmdir "$(lock_dir "$env")" 2>/dev/null || true
    printf '%s: stopped\n' "$env"
  fi
}

start() {
  local env pid signature
  env="$1"
  if managed_pid "$env"; then
    printf '%s 已在运行 (pid %s)\n' "$env" "$(read_pid "$env")" >&2
    return 1
  fi
  command_for "$env"
  mkdir -p "$RUN_DIR"
  rmdir "$(lock_dir "$env")" 2>/dev/null || true
  if ! mkdir "$(lock_dir "$env")" 2>/dev/null; then
    printf '%s 已有启动锁，拒绝重复启动\n' "$env" >&2
    return 1
  fi
  [[ -e "$(pid_file "$env")" ]] && rm -f -- "$(pid_file "$env")"
  nohup "${COMMAND[@]}" run >>"$(log_file "$env")" 2>&1 &
  pid="$!"
  signature="$(process_signature "$pid")" || {
    kill "$pid" 2>/dev/null || true
    rmdir "$(lock_dir "$env")" 2>/dev/null || true
    printf '%s 启动失败\n' "$env" >&2
    return 1
  }
  printf '%s\n%s\n' "$pid" "$signature" >"$(pid_file "$env")"
  printf '%s started (pid %s)\n' "$env" "$pid"
}

stop() {
  local env pid
  env="$1"
  pid="$(read_pid "$env")"
  if managed_pid "$env"; then
    kill "$pid"
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -KILL "$pid"
    fi
  elif [[ -e "$(pid_file "$env")" ]]; then
    rm -f -- "$(pid_file "$env")"
    rmdir "$(lock_dir "$env")" 2>/dev/null || true
    printf '%s: PID 记录与进程不匹配，未发送终止信号\n' "$env" >&2
    return 1
  fi
  rm -f -- "$(pid_file "$env")"
  rmdir "$(lock_dir "$env")" 2>/dev/null || true
  printf '%s stopped\n' "$env"
}

main() {
  local action="${1:-}" env="${2:-}"
  case "$action" in
    status) status_one dev; status_one prod ;;
    start|run|stop|restart)
      [[ "$env" == dev || "$env" == prod ]] || { usage; return 2; }
      case "$action" in
        start) start "$env" ;;
        run) run_foreground "$env" ;;
        stop) stop "$env" ;;
        restart) stop "$env"; start "$env" ;;
      esac
      ;;
    *) usage; return 2 ;;
  esac
}

main "$@"
