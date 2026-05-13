# Bash 脚本 (Wrappers)

cortex 把 20 个 slash command 中常用的 17 个包装成独立 bash 脚本, 部署在 `~/.cortex/scripts/`。无入参, 一行调用。

每个脚本内部:
1. 读 `~/.cortex/config.json` 拿 `vault` / `settings` / `install_path`
2. 走 `cortex_stream_runner` (rich UI on stderr) + `cx_filter_stream` (final result.text on stdout)
3. 调 `claude --settings <s> -p "/cortex:<name>"` 触发 slash command
4. 完成后自动 `git commit` vault 变更 (不 push)

## 脚本清单

| 脚本 | 对应 slash command | 用途 |
|------|---------------------|------|
| `init.sh` | `/cortex:init` | 初始化 vault (首次安装时跑) |
| `install_cron.sh` | `/cortex:install_cron` | 部署定时任务 |
| `config.sh` | `/cortex:config` | 交互式编辑 `~/.cortex/config.json` |
| `update.sh` | `/cortex:update` | 更新插件 |
| `doctor.sh` | `/cortex:doctor` | 体检 |
| `lint.sh` | `/cortex:lint` | 全自动修复 lint |
| `refactor.sh` | `/cortex:refactor` | 重构 vault |
| `search.sh` | `/cortex:search` | 搜索 |
| `save.sh` | `/cortex:save` | 落档 |
| `ingest.sh` | `/cortex:ingest` | 深度摄取当前目录 |
| `recall.sh` | `/cortex:recall` | 召回记忆 |
| `memory.sh` | `/cortex:memory` | 记忆管理 |
| `promote.sh` | `/cortex:promote` | 提升记忆等级 |
| `forget.sh` | `/cortex:forget` | 遗忘 |
| `consolidate.sh` | `/cortex:consolidate` | 整合 ledger |
| `dashboard.sh` | `/cortex:dashboard` | 刷新仪表盘 |
| `fold.sh` | `/cortex:fold` | 折叠长 log |

## 使用

```bash
# 直接跑
bash ~/.cortex/scripts/lint.sh

# 或 PATH 添加 ~/.cortex/scripts/ 后
lint.sh
```

stdout 输出最终 result text, stderr 显示 rich 实时进度。

## 输出协议

- **stdout**: 仅 final result.text 纯文本 (用 `>` 重定向到文件 OK)
- **stderr**: rich UI 渲染的实时进度 (顺序输出, 不截断不刷新)
- **exit code**: 0 成功, 非 0 失败 (具体码见 `~/.cortex/scripts/_lib/colors.sh`)

## 环境变量 (可选)

| 变量 | 用途 |
|------|------|
| `CORTEX_JOB_LABEL` | 自定义日志 label (默认 wrapper 名) |
| `CORTEX_STREAM_TEE_FILE` | 把 raw NDJSON 同步写到指定文件 (调试用) |
| `CORTEX_TIMEOUT` | claude 调用超时秒数 (默认 0 = 不超时) |

**禁用** 的配置类 env var: `OBSIDIAN_VAULT` / `CORTEX_VAULT` / `CORTEX_LANG` / `CORTEX_INSTALL_PATH` / `CORTEX_SETTINGS` — 全部从 `~/.cortex/config.json` 读取。

## cron / launchd / GitHub Actions

通过 `bash ~/.cortex/scripts/install_cron.sh` 注册的定时任务最终调用同一批脚本。详见 [周期任务](周期任务.md)。

## 自定义路径

config.json 可改 `install_path` (插件源根) + `target_dir` (wrapper 部署目录, 默认 `~/.cortex/scripts/`)。
