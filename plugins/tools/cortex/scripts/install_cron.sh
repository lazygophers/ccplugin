#!/usr/bin/env bash
# cortex/scripts/install_cron.sh
#
# 不自动写用户 crontab/launchd, 仅打印 snippet 供用户自决复制。
# 支持: macOS launchd / Linux cron / GitHub Actions
#
# 用法:
#   bash install_cron.sh [launchd|cron|gha]      # 默认 cron
#
# 任务清单 (prd §7 M6):
#   daily   01:00  cortex-lint --auto-fix
#   weekly  Sun 02:00  cortex-fold (log rollup)
#   weekly  Sun 02:30  cortex-dashboard refresh
#
# 所有命令以 `claude -p "<phrase>"` 触发对应 skill, 用户需先安装 claude CLI。

set -euo pipefail

KIND="${1:-cron}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
VAULT="${OBSIDIAN_VAULT:-$HOME/persons/knowledge/obsidian}"

print_cron() {
  cat <<EOF
# ===== cortex cron snippet (Linux/macOS cron) =====
# 复制以下行到 'crontab -e':

# daily lint with autofix at 01:00
0 1 * * * /usr/bin/env python3 "${PLUGIN_ROOT}/lint/run.py" --vault "${VAULT}" --fix > "\$HOME/.cache/cortex/lint-\$(date +\%Y\%m\%d).json" 2>&1

# weekly log fold at Sunday 02:00
0 2 * * 0 /usr/bin/env python3 "${PLUGIN_ROOT}/refactor/fold.py" --vault "${VAULT}" --days 7 --apply >> "\$HOME/.cache/cortex/fold.log" 2>&1

# weekly dashboard refresh at Sunday 02:30 (claude CLI required)
30 2 * * 0 claude -p "/cortex-dashboard refresh all" >> "\$HOME/.cache/cortex/dashboard.log" 2>&1
EOF
}

print_launchd() {
  cat <<EOF
# ===== cortex launchd plist (macOS) =====
# 保存为 ~/Library/LaunchAgents/dev.lazygophers.cortex.daily-lint.plist
# 然后: launchctl load ~/Library/LaunchAgents/dev.lazygophers.cortex.daily-lint.plist

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>dev.lazygophers.cortex.daily-lint</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>python3</string>
    <string>${PLUGIN_ROOT}/lint/run.py</string>
    <string>--vault</string>
    <string>${VAULT}</string>
    <string>--fix</string>
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
#   - dev.lazygophers.cortex.weekly-fold (Hour=2, Minute=0, Weekday=0)
#   - dev.lazygophers.cortex.weekly-dashboard (Hour=2, Minute=30, Weekday=0)
EOF
}

print_gha() {
  cat <<'EOF'
# ===== cortex GitHub Actions workflow =====
# 保存为 .github/workflows/cortex-cron.yml (在你的 vault 仓库)
# 要求 vault 是 GitHub repo, 并配置 secrets.OBSIDIAN_API_KEY 等

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
        run: python3 lint/run.py --vault . --fix > lint-report.json
      - uses: actions/upload-artifact@v4
        with: { name: lint-report, path: lint-report.json }

  fold:
    if: github.event.schedule == '0 2 * * 0'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: cortex fold
        run: python3 refactor/fold.py --vault . --days 7 --apply
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
    echo "usage: $0 [cron|launchd|gha]" >&2
    exit 2
    ;;
esac

cat <<'EOF'

# ----------------------------------------------------------------------
# 注意:
# 1. 本脚本仅打印 snippet, 不写入任何用户配置 (跨平台风险)
# 2. 选定方案后用户自行复制安装
# 3. PLUGIN_ROOT / OBSIDIAN_VAULT 已被解析为当前绝对路径
# 4. 验证: 复制完成后立即手跑一次, 确认输出与权限正常
# ----------------------------------------------------------------------
EOF
