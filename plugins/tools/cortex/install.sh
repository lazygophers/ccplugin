#!/usr/bin/env bash
# cortex/install.sh — 一键安装入口
#
# 调度流程:
#   1. 探测 marketplace 安装路径 (CORTEX_INSTALL_PATH > 脚本所在目录)
#   2. 收集 vault / lang / settings (交互 prompt 或 flag)
#   3. 写入 ~/.cortex/config.json (调 scripts/cortex_config.py init)
#   4. 生成 ~/.cortex/scripts/*.sh 七件套 (调 scripts/install_wrappers.sh)
#   5. 可选: 运行 ~/.cortex/scripts/install_cron.sh 安装 cron snippet
#
# Usage:
#   ./install.sh                              # 交互模式
#   ./install.sh --non-interactive --vault PATH [--lang CODE] [--settings PATH] [--no-cron]
#   ./install.sh --help
#
# Exit codes:
#   0   success
#   2   usage error (缺 vault 在非交互模式)
#   其它  下游脚本传播

set -euo pipefail

# ── 色彩输出 ────────────────────────────────────────────────────────
# 仅当 stderr 是 tty 且未设 NO_COLOR 时启用 ANSI
if [[ -t 2 && -z "${NO_COLOR:-}" ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_DIM=$'\033[2m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_BLUE=$'\033[34m'
  C_MAGENTA=$'\033[35m'
  C_CYAN=$'\033[36m'
else
  C_RESET=""; C_BOLD=""; C_DIM=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_MAGENTA=""; C_CYAN=""
fi

_tag() { printf '%s[cortex]%s' "$C_CYAN" "$C_RESET"; }
log_info()  { printf '%s %s\n'           "$(_tag)" "$*" >&2; }
log_step()  { printf '%s %s▸%s %s\n'     "$(_tag)" "$C_BLUE"    "$C_RESET" "$*" >&2; }
log_ok()    { printf '%s %s✓%s %s\n'     "$(_tag)" "$C_GREEN"   "$C_RESET" "$*" >&2; }
log_warn()  { printf '%s %s⚠%s  %s\n'    "$(_tag)" "$C_YELLOW"  "$C_RESET" "$*" >&2; }
log_error() { printf '%s %s✗%s %s\n'     "$(_tag)" "$C_RED"     "$C_RESET" "$*" >&2; }
log_hint()  { printf '%s   %s%s%s\n'     "$(_tag)" "$C_DIM"     "$*" "$C_RESET" >&2; }

print_help() {
  cat <<'EOF'
cortex install.sh — 一键安装 cortex 共享配置 + wrapper

USAGE:
  ./install.sh                              # 交互模式
  ./install.sh --non-interactive [flags]    # 非交互模式
  ./install.sh --help

FLAGS:
  --vault <path>            vault 绝对路径 (非交互必填)
  --lang <code>             语言代码 (默认 zh-CN)
  --settings <path>         claude settings 路径 (默认 ~/.claude/settings.json)
  --no-cron                 跳过 cron 安装步骤
  --non-interactive         不弹任何 prompt
  -h, --help                显示本帮助

EXAMPLES:
  ./install.sh
  ./install.sh --non-interactive --vault ~/Documents/vault --no-cron
EOF
}

NON_INTERACTIVE=0
VAULT=""
LANG_CODE=""
SETTINGS=""
NO_CRON=0
INSTALL_CRON_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault) VAULT="${2:-}"; shift 2 ;;
    --vault=*) VAULT="${1#*=}"; shift ;;
    --lang) LANG_CODE="${2:-}"; shift 2 ;;
    --lang=*) LANG_CODE="${1#*=}"; shift ;;
    --settings) SETTINGS="${2:-}"; shift 2 ;;
    --settings=*) SETTINGS="${1#*=}"; shift ;;
    --no-cron) NO_CRON=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) log_error "unknown arg: $1"; exit 2 ;;
  esac
done

# 探测 plugin 树; curl|bash 远端运行时通过 claude CLI 装/升 marketplace + plugin
CORTEX_MARKETPLACE_NAME="${CORTEX_MARKETPLACE_NAME:-ccplugin-market}"
CORTEX_MARKETPLACE_SOURCE="${CORTEX_MARKETPLACE_SOURCE:-lazygophers/ccplugin}"
CORTEX_PLUGIN_NAME="${CORTEX_PLUGIN_NAME:-cortex}"

claude_marketplace_install_location() {
  # 输出 marketplace 的 installLocation; 找不到则退出 1
  local name="$1"
  claude plugins marketplace list --json 2>/dev/null | python3 -c '
import json, sys
name = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for m in data:
    if m.get("name") == name:
        loc = m.get("installLocation") or ""
        if loc:
            print(loc)
            sys.exit(0)
sys.exit(1)
' "$name"
}

claude_plugin_installed() {
  # 检查 <plugin>@<marketplace> 是否在 plugins list 中
  local pid="$1"
  claude plugins list --json 2>/dev/null | python3 -c '
import json, sys
pid = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for p in data:
    if p.get("id") == pid:
        sys.exit(0)
sys.exit(1)
' "$pid"
}

bootstrap_via_claude() {
  command -v claude >/dev/null 2>&1 || {
    log_error "需要 claude CLI 来 bootstrap, 未找到 claude 命令"
    log_hint "装 Claude Code: https://github.com/anthropics/claude-code"
    return 1
  }

  # 1. marketplace: 已存在 → update, 否则 add
  local mkt_loc
  if mkt_loc="$(claude_marketplace_install_location "$CORTEX_MARKETPLACE_NAME")"; then
    log_step "marketplace 已存在 (${C_BOLD}${CORTEX_MARKETPLACE_NAME}${C_RESET}), 更新中"
    claude plugins marketplace update "$CORTEX_MARKETPLACE_NAME" >&2 || {
      log_warn "marketplace update 非零, 继续用本地副本"
    }
  else
    log_step "添加 marketplace: ${C_BOLD}${CORTEX_MARKETPLACE_SOURCE}${C_RESET}"
    claude plugins marketplace add "$CORTEX_MARKETPLACE_SOURCE" >&2 || return 1
    mkt_loc="$(claude_marketplace_install_location "$CORTEX_MARKETPLACE_NAME")" || {
      log_error "marketplace add 后仍找不到 $CORTEX_MARKETPLACE_NAME"
      return 1
    }
  fi

  # 2. plugin: 已装 → update, 否则 install
  local pid="${CORTEX_PLUGIN_NAME}@${CORTEX_MARKETPLACE_NAME}"
  if claude_plugin_installed "$pid"; then
    log_step "plugin 已装 (${C_BOLD}${pid}${C_RESET}), 更新中"
    claude plugins update "$pid" >&2 || {
      log_warn "plugin update 非零, 继续用本地副本"
    }
  else
    log_step "安装 plugin: ${C_BOLD}${pid}${C_RESET}"
    claude plugins install "$pid" >&2 || return 1
  fi

  # 3. plugin 源码路径 = marketplace installLocation/plugins/tools/<plugin>
  local candidate="$mkt_loc/plugins/tools/$CORTEX_PLUGIN_NAME"
  if [[ -f "$candidate/scripts/cortex_config.py" ]]; then
    printf '%s' "$candidate"
    return 0
  fi
  log_error "在 $candidate 找不到 scripts/cortex_config.py"
  return 1
}

resolve_install_path() {
  if [[ -n "${CORTEX_INSTALL_PATH:-}" ]]; then
    printf '%s' "$CORTEX_INSTALL_PATH"
    return 0
  fi
  local src="${BASH_SOURCE[0]:-}"
  if [[ -n "$src" && -f "$src" ]]; then
    local dir
    dir="$(cd "$(dirname "$src")" 2>/dev/null && pwd || true)"
    if [[ -n "$dir" && -f "$dir/scripts/cortex_config.py" ]]; then
      printf '%s' "$dir"
      return 0
    fi
  fi
  bootstrap_via_claude
}

if ! INSTALL_PATH="$(resolve_install_path)"; then
  log_error "未找到 plugin 树且 claude CLI bootstrap 失败"
  log_hint "手动装: claude plugins marketplace add $CORTEX_MARKETPLACE_SOURCE && claude plugins install ${CORTEX_PLUGIN_NAME}@${CORTEX_MARKETPLACE_NAME}"
  log_hint "或设置 CORTEX_INSTALL_PATH 指向已有 plugin 路径"
  exit 2
fi

if [[ ! -d "$INSTALL_PATH" ]]; then
  log_error "install-path 不是目录: $INSTALL_PATH"
  exit 2
fi
if [[ ! -f "$INSTALL_PATH/scripts/cortex_config.py" ]]; then
  log_error "在 $INSTALL_PATH 未找到 scripts/cortex_config.py"
  exit 2
fi

log_ok "cortex 安装路径: ${C_BOLD}${INSTALL_PATH}${C_RESET}"

# 探测 tty: curl|bash 时 stdin 是脚本管道, prompt 必须从 /dev/tty 读
# 注意: `exec 3</dev/tty 2>/dev/null` 会把当前 shell stderr 永久重定向到 /dev/null,
# 必须用 group `{ ...; } 2>/dev/null` 把 stderr 重定向限制在 group 内。
TTY_FD=""
if [[ "$NON_INTERACTIVE" != "1" ]]; then
  if { exec 3</dev/tty; } 2>/dev/null; then
    TTY_FD=3
  else
    log_warn "无 /dev/tty, 自动切换 --non-interactive"
    NON_INTERACTIVE=1
  fi
fi

prompt_value() {
  local label="$1" default="$2"
  local suffix=""
  [[ -n "$default" ]] && suffix=" ${C_DIM}[${default}]${C_RESET}"
  local raw
  read -r -u "$TTY_FD" -p "$(_tag) ${C_BLUE}?${C_RESET} ${C_BOLD}${label}${C_RESET}${suffix}: " raw || raw=""
  raw="${raw## }"
  raw="${raw%% }"
  if [[ -z "$raw" && -n "$default" ]]; then
    printf '%s' "$default"
  else
    printf '%s' "$raw"
  fi
}

prompt_yes_no() {
  local label="$1" default="$2"  # default = Y or n
  local suffix
  if [[ "$default" == "Y" ]]; then suffix=" ${C_DIM}[Y/n]${C_RESET}"; else suffix=" ${C_DIM}[y/N]${C_RESET}"; fi
  local raw
  read -r -u "$TTY_FD" -p "$(_tag) ${C_BLUE}?${C_RESET} ${C_BOLD}${label}${C_RESET}${suffix}: " raw || raw=""
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "$raw" ]]; then
    [[ "$default" == "Y" ]] && return 0 || return 1
  fi
  [[ "$raw" == "y" || "$raw" == "yes" ]] && return 0 || return 1
}

# 收集字段
if [[ "$NON_INTERACTIVE" == "1" ]]; then
  if [[ -z "$VAULT" ]]; then
    echo "[install.sh] 非交互模式缺 --vault" >&2
    echo "  curl|bash 用例: curl ... | bash -s -- --non-interactive --vault \$HOME/path/to/vault" >&2
    exit 2
  fi
else
  default_vault="${VAULT:-${CORTEX_VAULT:-${OBSIDIAN_VAULT:-}}}"
  while :; do
    VAULT="$(prompt_value "vault 路径" "$default_vault")"
    if [[ -z "$VAULT" ]]; then
      log_warn "vault 不能为空, 请重试"
      continue
    fi
    # 展开 ~
    VAULT="${VAULT/#\~/$HOME}"
    if [[ ! -d "$VAULT" ]]; then
      log_warn "路径不存在或非目录: ${C_BOLD}${VAULT}${C_RESET}, 请重试"
      continue
    fi
    break
  done

  default_lang="${LANG_CODE:-${CORTEX_LANG:-zh-CN}}"
  LANG_CODE="$(prompt_value "lang" "$default_lang")"

  default_settings="${SETTINGS:-${CORTEX_SETTINGS:-$HOME/.claude/settings.json}}"
  SETTINGS="$(prompt_value "claude settings 路径" "$default_settings")"
  SETTINGS="${SETTINGS/#\~/$HOME}"
fi

# 展开 ~ (非交互模式也补一下)
VAULT="${VAULT/#\~/$HOME}"
[[ -n "$SETTINGS" ]] && SETTINGS="${SETTINGS/#\~/$HOME}"

# 调 cortex_config.py init 写 config
init_args=(--non-interactive --install-path "$INSTALL_PATH" --vault "$VAULT")
[[ -n "$LANG_CODE" ]] && init_args+=(--lang "$LANG_CODE")
[[ -n "$SETTINGS" ]] && init_args+=(--settings "$SETTINGS")

log_step "写入 ${C_BOLD}~/.cortex/config.json${C_RESET}"
python3 "$INSTALL_PATH/scripts/cortex_config.py" init "${init_args[@]}"

# 生成 wrapper
log_step "生成 ${C_BOLD}~/.cortex/scripts/*.sh${C_RESET} wrapper"
bash "$INSTALL_PATH/scripts/install_wrappers.sh" --install-path "$INSTALL_PATH"

# 可选 cron 安装
do_cron=0
if [[ "$NO_CRON" == "1" ]]; then
  do_cron=0
elif [[ "$NON_INTERACTIVE" == "1" ]]; then
  do_cron=0
else
  if prompt_yes_no "现在通过 wrapper 安装 cron snippet?" "n"; then
    do_cron=1
  fi
fi

if [[ "$do_cron" == "1" ]]; then
  log_step "调用 ${C_BOLD}~/.cortex/scripts/install_cron.sh${C_RESET}"
  bash "$HOME/.cortex/scripts/install_cron.sh" || {
    log_warn "install_cron.sh 退出非零, 跳过 (cron 仍可手动跑)"
  }
fi

printf '\n'
printf '%s %s✓ cortex 安装完成%s\n'           "$(_tag)" "$C_GREEN$C_BOLD" "$C_RESET" >&2
printf '%s   %sconfig%s:   %s~/.cortex/config.json%s\n'  "$(_tag)" "$C_DIM" "$C_RESET" "$C_BOLD" "$C_RESET" >&2
printf '%s   %swrappers%s: %s~/.cortex/scripts/%s\n'     "$(_tag)" "$C_DIM" "$C_RESET" "$C_BOLD" "$C_RESET" >&2
printf '\n'
printf '%s %sNext:%s\n'                                   "$(_tag)" "$C_CYAN$C_BOLD" "$C_RESET" >&2
printf '%s   %s~/.cortex/scripts/doctor.sh%s         %s# 健康检查%s\n'      "$(_tag)" "$C_BOLD" "$C_RESET" "$C_DIM" "$C_RESET" >&2
printf '%s   %s~/.cortex/scripts/update.sh%s         %s# 更新插件%s\n'      "$(_tag)" "$C_BOLD" "$C_RESET" "$C_DIM" "$C_RESET" >&2
printf '%s   %s~/.cortex/scripts/install_cron.sh%s   %s# 安装周期任务%s\n'  "$(_tag)" "$C_BOLD" "$C_RESET" "$C_DIM" "$C_RESET" >&2
