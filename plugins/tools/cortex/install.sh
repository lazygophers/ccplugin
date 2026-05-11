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
  --settings <path>         claude settings 路径 (默认 ~/.claude/settings.glm-4.5-flash.json)
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
    *) echo "[install.sh] unknown arg: $1" >&2; exit 2 ;;
  esac
done

# 探测 marketplace 安装路径
if [[ -n "${CORTEX_INSTALL_PATH:-}" ]]; then
  INSTALL_PATH="$CORTEX_INSTALL_PATH"
else
  INSTALL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

if [[ ! -d "$INSTALL_PATH" ]]; then
  echo "[install.sh] install-path 不是目录: $INSTALL_PATH" >&2
  exit 2
fi
if [[ ! -f "$INSTALL_PATH/scripts/cortex_config.py" ]]; then
  echo "[install.sh] 在 $INSTALL_PATH 未找到 scripts/cortex_config.py" >&2
  exit 2
fi

echo "[install.sh] cortex 安装路径: $INSTALL_PATH"

prompt_value() {
  local label="$1" default="$2"
  local suffix=""
  [[ -n "$default" ]] && suffix=" [$default]"
  local raw
  read -r -p "${label}${suffix}: " raw || raw=""
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
  if [[ "$default" == "Y" ]]; then suffix=" [Y/n]"; else suffix=" [y/N]"; fi
  local raw
  read -r -p "${label}${suffix}: " raw || raw=""
  raw="${raw,,}"
  if [[ -z "$raw" ]]; then
    [[ "$default" == "Y" ]] && return 0 || return 1
  fi
  [[ "$raw" == "y" || "$raw" == "yes" ]] && return 0 || return 1
}

# 收集字段
if [[ "$NON_INTERACTIVE" == "1" ]]; then
  if [[ -z "$VAULT" ]]; then
    echo "[install.sh] 非交互模式缺 --vault" >&2
    exit 2
  fi
else
  default_vault="${VAULT:-${CORTEX_VAULT:-${OBSIDIAN_VAULT:-}}}"
  while :; do
    VAULT="$(prompt_value "vault 路径" "$default_vault")"
    if [[ -z "$VAULT" ]]; then
      echo "  vault 不能为空, 请重试" >&2
      continue
    fi
    # 展开 ~
    VAULT="${VAULT/#\~/$HOME}"
    if [[ ! -d "$VAULT" ]]; then
      echo "  路径不存在或非目录: $VAULT, 请重试" >&2
      continue
    fi
    break
  done

  default_lang="${LANG_CODE:-${CORTEX_LANG:-zh-CN}}"
  LANG_CODE="$(prompt_value "lang" "$default_lang")"

  default_settings="${SETTINGS:-${CORTEX_SETTINGS:-$HOME/.claude/settings.glm-4.5-flash.json}}"
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

echo "[install.sh] 写入 ~/.cortex/config.json"
python3 "$INSTALL_PATH/scripts/cortex_config.py" init "${init_args[@]}"

# 生成 wrapper
echo "[install.sh] 生成 ~/.cortex/scripts/*.sh wrapper"
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
  echo "[install.sh] 调用 ~/.cortex/scripts/install_cron.sh"
  bash "$HOME/.cortex/scripts/install_cron.sh" || {
    echo "[install.sh] install_cron.sh 退出非零, 跳过 (cron 仍可手动跑)" >&2
  }
fi

cat <<EOF

✓ cortex 安装完成
- config: ~/.cortex/config.json
- wrappers: ~/.cortex/scripts/

Next:
  ~/.cortex/scripts/doctor.sh         # 健康检查
  ~/.cortex/scripts/update.sh         # 更新插件
  ~/.cortex/scripts/install_cron.sh   # 安装周期任务
EOF
