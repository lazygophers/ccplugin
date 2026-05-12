#!/usr/bin/env bash
# cortex/scripts/install_cron.sh
#
# 不自动写用户 crontab/launchd, 仅打印 snippet 供用户自决复制。
# 支持: macOS launchd / Linux cron / GitHub Actions
#
# 用法:
#   bash install_cron.sh [--plugin-root <path>] [launchd|cron|gha]   # 默认 cron
#   bash install_cron.sh --help
#
# 任务清单 (prd §7 M6):
#   daily   01:00       cortex lint
#   weekly  Sun 02:00   cortex fold (log rollup)
#   weekly  Sun 02:30   cortex dashboard refresh
#
# 所有命令以 `claude --bare -p` 触发对应 skill, 用户需先安装 claude CLI。

set -euo pipefail

print_help() {
  cat <<'EOF'
install_cron.sh — 打印 cortex 周期任务 snippet (不写 crontab/launchd)

USAGE:
  bash install_cron.sh [--plugin-root <path>] [launchd|cron|gha]
  bash install_cron.sh --help

OPTIONS:
  --plugin-root <path>   显式指定 cortex 插件根路径 (优先级最高)
  --help, -h             显示本帮助

PLUGIN_ROOT 解析优先级 (从高到低):
  1. --plugin-root <path>                  命令行覆盖
  2. ~/.cortex/config.json .install_path   配置 (env-free per PRD)
  3. ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex      (主, 默认)
  4. ~/.config/claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex (XDG 兜底)
  5. $CLAUDE_PLUGIN_ROOT                   (Claude Code 平台契约, 由主线注入)
  6. fallback: 脚本所在源码路径 + stderr 警告

snippet 输出: PLUGIN_ROOT 已被解析为绝对路径字符串 (非变量占位), 用户可直接粘贴到 crontab。
GHA snippet 例外: 使用 \${GITHUB_WORKSPACE} 占位, 由 CI 环境注入。
EOF
}

# ----------------------------------------------------------------------
# resolve_install_path
#
# 输出 (stdout): 解析后的绝对路径
# 副作用 (stderr): fallback 时输出警告
# 入参:
#   $1 = override path (来自 --plugin-root, 可空)
# ----------------------------------------------------------------------
resolve_install_path() {
  local override="${1:-}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

  # 1. 命令行覆盖
  if [[ -n "$override" ]]; then
    printf '%s\n' "$override"
    return 0
  fi

  # 2. ~/.cortex/config.json install_path (env-free per PRD)
  if [[ -f "$HOME/.cortex/config.json" ]] && command -v jq >/dev/null 2>&1; then
    local from_cfg
    from_cfg=$(jq -r '.install_path // empty' "$HOME/.cortex/config.json" 2>/dev/null)
    if [[ -n "$from_cfg" ]]; then
      printf '%s\n' "$from_cfg"
      return 0
    fi
  fi

  # 3. 主 marketplace 路径
  local primary="$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  if [[ -d "$primary" ]]; then
    printf '%s\n' "$primary"
    return 0
  fi

  # 4. XDG 兜底
  local xdg="$HOME/.config/claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex"
  if [[ -d "$xdg" ]]; then
    printf '%s\n' "$xdg"
    return 0
  fi

  # 5. CLAUDE_PLUGIN_ROOT (CC 主线注入)
  if [[ -n "${CLAUDE_PLUGIN_ROOT:-}" ]]; then
    printf '%s\n' "$CLAUDE_PLUGIN_ROOT"
    return 0
  fi

  # 6. fallback: 源码路径 + 警告
  printf '%s\n' "$script_dir"
  printf '[install_cron.sh] WARNING: 未检测到 marketplace 安装, cron 任务可能因路径无效失败\n' >&2
  printf '[install_cron.sh] WARNING: fallback 到源码路径 %s\n' "$script_dir" >&2
  printf '[install_cron.sh] WARNING: 请通过 --plugin-root 或在 ~/.cortex/config.json 设置 install_path 指定 marketplace 安装路径\n' >&2
}

# -------- 参数解析 --------
KIND=""
OVERRIDE_ROOT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugin-root)
      OVERRIDE_ROOT="${2:-}"
      shift 2
      ;;
    --plugin-root=*)
      OVERRIDE_ROOT="${1#*=}"
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    cron|launchd|gha)
      KIND="$1"
      shift
      ;;
    *)
      echo "usage: $0 [--plugin-root <path>] [cron|launchd|gha]" >&2
      exit 2
      ;;
  esac
done
KIND="${KIND:-cron}"

PLUGIN_ROOT="$(resolve_install_path "$OVERRIDE_ROOT")"

# Load ~/.cortex/config.json (env > config > fallback) so the printed snippets
# default to the user's configured vault/lang/settings. JSON syntax errors
# fail-fast here (cortex_config_init exits 1 with stderr message).
# shellcheck source=./lib/config.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/config.sh"
cortex_config_init

# vault: config only (env-free per PRD).
VAULT="$(cx_get_vault)"
if [[ -z "$VAULT" ]]; then
  echo "[install_cron.sh] no vault configured: set 'vault' in ~/.cortex/config.json" >&2
  exit 3
fi

# lang/settings flow into the printed snippet so users get the same resolution
# rules as cron/run.sh — but as CLI flags (not env exports).
LANG_OVERRIDE="$(cx_config_get lang "")"
SETTINGS="$(cx_config_get settings "")"

print_cron() {
  cat <<EOF
# ===== cortex cron snippet (Linux/macOS cron) =====
# 复制以下行到 'crontab -e':

# 走 scripts/cron/<job>.sh wrapper (claude --bare, lock + timeout + log rotation)
# 注意: PLUGIN_ROOT 已硬编码为 marketplace 绝对路径, 适用于 cron daemon 环境

# daily lint at 01:00
0 1 * * * bash "~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cron/lint.sh" --vault "${VAULT}"

# weekly log fold at Sunday 02:00
0 2 * * 0 bash "~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cron/fold.sh" --vault "${VAULT}"

# weekly dashboard refresh at Sunday 02:30
30 2 * * 0 bash "~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cron/dashboard.sh" --vault "${VAULT}"
EOF
}

print_launchd() {
  cat <<EOF
# ===== cortex launchd plist (macOS) =====
# 保存为 ~/Library/LaunchAgents/dev.lazygophers.cortex.daily-lint.plist
# 然后: launchctl load ~/Library/LaunchAgents/dev.lazygophers.cortex.daily-lint.plist
# 注意: PLUGIN_ROOT 已硬编码为 marketplace 绝对路径

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>dev.lazygophers.cortex.daily-lint</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cron/lint.sh</string>
    <string>--vault</string>
    <string>${VAULT}</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>1</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${HOME}/.cache/cortex/lint.log</string>
  <key>StandardErrorPath</key>
  <string>${HOME}/.cache/cortex/lint.err</string>
</dict>
</plist>

# 同样模板可派生:
#   - dev.lazygophers.cortex.weekly-fold (Hour=2, Minute=0, Weekday=0, fold.sh)
#   - dev.lazygophers.cortex.weekly-dashboard (Hour=2, Minute=30, Weekday=0, dashboard.sh)
EOF
}

print_gha() {
  cat <<'EOF'
# ===== cortex GitHub Actions workflow =====
# 保存为 .github/workflows/cortex-cron.yml (在你的 vault 仓库)
# 要求 vault 是 GitHub repo, 并配置 secrets.OBSIDIAN_API_KEY 等
#
# 注意: CI 环境路径与本机 marketplace 不同。下方 ${GITHUB_WORKSPACE} 由
# Actions runner 注入, 指向 checkout 后的 vault 仓库根。若你的 cortex
# 插件 checkout 到子目录, 请显式调整路径。

name: cortex-cron

on:
  schedule:
    - cron: '0 1 * * *'    # daily lint
    - cron: '0 2 * * 0'    # weekly fold
  workflow_dispatch:

jobs:
  lint:
    if: github.event.schedule == '0 1 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: cortex lint
        run: bash ${GITHUB_WORKSPACE}/plugins/tools/cortex/scripts/cron/lint.sh
      - uses: actions/upload-artifact@v4
        with: { name: lint-report, path: ~/.cache/cortex/cron/ }

  fold:
    if: github.event.schedule == '0 2 * * 0'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: cortex fold
        run: bash ${GITHUB_WORKSPACE}/plugins/tools/cortex/scripts/cron/fold.sh
      - name: commit
        run: |
          git config user.name "cortex-bot"
          git config user.email "cortex@noreply.local"
          git add -A
          git diff --quiet --staged || git commit -m "cortex: weekly fold"
          git push
EOF
}

case "$KIND" in
  cron)    print_cron ;;
  launchd) print_launchd ;;
  gha)     print_gha ;;
  *)
    echo "usage: $0 [--plugin-root <path>] [cron|launchd|gha]" >&2
    exit 2
    ;;
esac

cat <<EOF

# ----------------------------------------------------------------------
# 注意:
# 1. 本脚本仅打印 snippet, 不写入任何用户配置 (跨平台风险)
# 2. 选定方案后用户自行复制安装
# 3. PLUGIN_ROOT = ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex
# 4. vault = ${VAULT} (from ~/.cortex/config.json)
# 5. 验证: 复制完成后立即手跑一次, 确认输出与权限正常
# ----------------------------------------------------------------------
EOF
