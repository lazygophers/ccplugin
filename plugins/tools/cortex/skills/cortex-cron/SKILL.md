---
name: cortex-cron
description: 注册 cortex 周期任务 (lint/fold/dashboard) 到 launchd/cron/GHA; dry-run + 确认; 支持 uninstall。仅显式触发。
argument-hint: "<install|status|uninstall|run> [job]"
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob
---

# cortex-cron

把 cortex 维护脚本注册到系统级定时器, 走 `claude --bare -p` 编程式调用。

## 触发场景

- cortex-install 流程末尾询问 cron 注册时调用本 skill
- 用户主动 "register cron" / "/cortex:cron install"
- 卸载: "uninstall cron"

## 平台检测顺序

1. **macOS** → launchd plist `~/Library/LaunchAgents/dev.lazygophers.cortex.<job>.plist`
2. **Linux** → systemd user timer (`~/.config/systemd/user/cortex-<job>.{service,timer}`) 或 crontab 行
3. **CI 环境** (检测 `$CI` env) → 输出 GHA workflow yaml, 不自动写

## 解析 PLUGIN_ROOT (marketplace 路径)

cron daemon 不继承 shell 环境, 故 snippet 中 `PLUGIN_ROOT` 必须是**绝对路径字符串**, 而非 `${PLUGIN_ROOT}` 占位。`install_cron.sh` 按下列优先级解析:

1. `--plugin-root <path>` 命令行覆盖
2. `$CORTEX_INSTALL_PATH` 环境变量
3. `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` (主, 默认)
4. `~/.config/claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` (XDG 兜底)
5. `$CLAUDE_PLUGIN_ROOT` (CC 主线注入)
6. fallback: 脚本所在源码路径 + stderr 警告

> 源码路径 (`/Users/foo/persons/.../plugins/tools/cortex`) 仅适合本地开发, cron 上下文不可达。优先用 marketplace 安装路径。

## 默认任务

| Job | 时机 | 命令 (snippet 中已替换为绝对路径) |
|-----|------|------|
| `lint` | daily 01:00 | `<PLUGIN_ROOT>/scripts/cron/lint.sh` |
| `fold` | weekly Sun 02:00 | `<PLUGIN_ROOT>/scripts/cron/fold.sh` |
| `dashboard` | weekly Sun 02:30 | `<PLUGIN_ROOT>/scripts/cron/dashboard.sh` |

其中 `<PLUGIN_ROOT>` 通常为 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex`。

每脚本走 `claude --bare --no-session-persistence --settings ~/.claude/settings.glm-4.5-flash.json -p "..."`, 见 research/01-claude-code-programmatic.md §E。

## 子命令

| 子命令 | 行为 |
|--------|------|
| `cortex-cron install [job]` | dry-run 显示要写入的 plist/crontab, 用户确认后落盘 |
| `cortex-cron status` | 列已注册任务 (launchctl list / systemctl --user list-timers / crontab -l 过滤) |
| `cortex-cron uninstall [job]` | 卸载指定 job 或全部 |
| `cortex-cron run <job>` | 立即手跑一次 (调试用) |

## 关键约束

1. **强制 dry-run + 确认** — 写 launchd / crontab 前必须打印 snippet, 用户确认才落盘。
2. **只读权限** — cron 任务默认 `--allowed-tools "Bash Read Glob"`, 不让 LLM 误改 vault。`--fix` 类操作不进 cron。
3. **超时 + 锁** — wrapper `scripts/cron/run.sh` 提供 `flock -n` + `timeout 600`。
4. **不写 user settings** — 仅写 LaunchAgents / systemd user / crontab 区域; 永不动 `~/.claude/settings.json`。
5. **CI 环境** — 检测到 `$CI` 时只打印 GHA yaml, 不真写。

## 卸载

```bash
cortex-cron uninstall          # 卸载全部 cortex.* 任务
cortex-cron uninstall lint     # 仅卸载 lint
```

## 输出示例

```text
$ cortex-cron install lint
[dry-run] launchd plist:
  ~/Library/LaunchAgents/dev.lazygophers.cortex.lint.plist
  schedule: 01:00 daily
  command: bash ${PLUGIN_ROOT}/scripts/cron/lint.sh --vault /Users/foo/obsidian

确认写入? [Y/n] y
✓ written. 加载: launchctl load ~/Library/LaunchAgents/dev.lazygophers.cortex.lint.plist
```
