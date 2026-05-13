# Bash 脚本 (Wrappers)

cortex 把 20 个 slash command 中常用的 17 个包装成独立 bash 脚本, 部署在 `~/.cortex/scripts/`。无入参, 一行调用。

每个脚本内部:
1. 读 `~/.cortex/config.json` 拿 `vault` / `settings` / `install_path`
2. 走 `cortex_stream_runner` (rich UI on stderr) + `cx_filter_stream` (final result.text on stdout)
3. 调 `claude --settings <s> -p "/cortex:<name>"` 触发 slash command
4. 完成后自动 `git commit` vault 变更 (不 push)

## 脚本清单

**范围标记**: 全局 (用户/系统级) · 当前目录 (PWD) · 知识库 (vault)

| 脚本 | 范围 | 对应 slash | 用途 |
|------|-----|-----------|------|
| `init.sh` | 全局+知识库 | `/cortex:init` | 初始化 vault (首次安装时跑) |
| `install_cron.sh` | 全局 | `/cortex:install_cron` | 部署定时任务到 launchd/cron/GHA |
| `config.sh` | 全局 | `/cortex:config` | 交互式编辑 `~/.cortex/config.json` |
| `update.sh` | 全局 | `/cortex:update` | 更新插件 (marketplace + wrappers) |
| `doctor.sh` | 全局+知识库 | `/cortex:doctor` | 体检 vault + 依赖 + 配置 |
| `lint.sh` | 知识库 | `/cortex:lint` | 全自动 lint 修复至 clean |
| `refactor.sh` | 知识库 | `/cortex:refactor` | 改名 / 合并 / 拆分 |
| `search.sh` | 知识库 | `/cortex:search` | 搜索 vault |
| `save.sh` | 知识库 | `/cortex:save` | 落档新笔记 |
| `ingest.sh` | 当前目录+知识库 | `/cortex:ingest` | 深度分析当前目录 → 落档到知识库 |
| `recall.sh` | 知识库 | `/cortex:recall` | 召回记忆 |
| `memory.sh` | 知识库 | `/cortex:memory` | 记忆管理 |
| `promote.sh` | 知识库 | `/cortex:promote` | 提升记忆等级 |
| `forget.sh` | 知识库 | `/cortex:forget` | 遗忘 |
| `consolidate.sh` | 知识库 | `/cortex:consolidate` | 整合 ledger |
| `dashboard.sh` | 知识库 | `/cortex:dashboard` | 刷新仪表盘 |
| `fold.sh` | 知识库 | `/cortex:fold` | 折叠长 log |

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
