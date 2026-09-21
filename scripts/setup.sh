#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
PID_FILE="$RUN_DIR/funserver-%s.pid"
LOG_FILE="$RUN_DIR/funserver-%s.log"
LOCK_DIR="$RUN_DIR/funserver-%s.lock"

usage() {
  printf '用法: %s {start|stop|restart|run|status} [dev|prod]\n' "${0##*/}" >&2
}

pid_file() { printf "$PID_FILE" "$1"; }
log_file() { printf "$LOG_FILE" "$1"; }
lock_dir() { printf "$LOCK_DIR" "$1"; }

read_pid() {
  local file
  file="$(pid_file "$1")"
  [[ -s "$file" ]] && tr -d '[:space:]' < "$file" || true
}

running_pid() {
  local env pid args
  env="$1"
  pid="$(read_pid "$env")"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$args" == *funserver* ]]
}

command_for() {
  case "$1" in
    dev)
      if command -v uv >/dev/null 2>&1; then
        printf '%s\0' uv run funserver
      else
        printf '%s\0' funserver
      fi
      ;;
    prod)
      command -v funserver >/dev/null 2>&1 || {
        printf '生产环境需要已安装的 funserver 命令\n' >&2
        return 1
      }
      printf '%s\0' funserver
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
  if running_pid "$env"; then
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
  local env pid command
  env="$1"
  if running_pid "$env"; then
    printf '%s 已在运行 (pid %s)\n' "$env" "$(read_pid "$env")" >&2
    return 1
  fi
  command_for "$env" >/dev/null
  rmdir "$(lock_dir "$env")" 2>/dev/null || true
  if ! mkdir "$(lock_dir "$env")" 2>/dev/null; then
    printf '%s 已有启动锁，拒绝重复启动\n' "$env" >&2
    return 1
  fi
  [[ -e "$(pid_file "$env")" ]] && rm -f -- "$(pid_file "$env")"
  command="$(command_for "$env" | tr '\0' ' ')"
  mkdir -p "$RUN_DIR"
  nohup bash -c "exec $command run" >>"$(log_file "$env")" 2>&1 &
  printf '%s\n' "$!" >"$(pid_file "$env")"
  printf '%s started (pid %s)\n' "$env" "$!"
}

stop() {
  local env pid
  env="$1"
  pid="$(read_pid "$env")"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    for _ in {1..20}; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" || true
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
