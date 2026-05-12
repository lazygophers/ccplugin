# PRD — wrapper 全部走 claude commands + 禁入参 + 全权限

## 3 约束 (user)

1. **bash 调 claude 全权限**: 不限 `--allowed-tools`, 启全部 (Bash/Read/Write/Edit/Glob/MCP/agents/skills/hooks)
2. **bash 禁入参**: 所有 wrapper 不接 CLI args, 跑就执行 (install 除外)
3. **bash 走 claude 调 commands**: 用 `claude -p "/cortex:<name>"`, 通过插件 slash command 触发, 不再 --bare + --append-system-prompt + 自定义 prompt

## 现状问题

- wrapper 用 `claude --bare ... -p "<prompt>" --allowed-tools "..." --append-system-prompt SKILL.md` 限制 + 注入
- 复杂 prompt 容易 AI 漫游 / 崩 (dashboard 实测 EXIT 1)
- 工具白名单限制反而让 AI 无法用 MCP 等

## 目标

1. 建 `commands/` 目录定义所有 cortex 命令
2. plugin.json 注册 commands
3. wrapper 重写: `exec claude -p "/cortex:<name>"` 无 --bare 无 --allowed-tools 无 args
4. 需参数的功能 (search/save/ingest/memory) 删 wrapper, 用户在 claude 内直接调 `/cortex:search <query>` 等

## 设计

### 1. commands 目录

新建 `plugins/tools/cortex/commands/`:

每个 `.md` 是一个 slash command:

#### `commands/lint.md`
```markdown
---
description: 跑 cortex vault lint --fix 强制对齐
---

# /cortex:lint

[AUTO_MODE strict: 禁止询问用户, 全自动决策, fail-fast]

按 cortex-lint SKILL 流程:
1. Bash 调 `cd $(jq -r .install_path ~/.cortex/config.json) && PYTHONPATH=. python3 -m lint.run --vault $(jq -r .vault ~/.cortex/config.json) --fix`
2. 解析 JSON 输出
3. 报告 fixed 数 + 各 rule hit

输出: rich callout summary。
```

#### `commands/dashboard.md`
```markdown
---
description: 刷新 cortex vault 仪表盘 (一次 1 页, 不漫游)
---

# /cortex:dashboard

[AUTO_MODE strict: 禁询问, 自动决策]

按 cortex-dashboard SKILL AUTO_MODE 严约束:
- Glob 仪表盘/*.md (cap 20)
- 每页仅读 frontmatter (前 30 行)
- 禁读 .jsonl/.md 全文
- 注入 <!-- DASH:BEGIN -->...<!-- DASH:END --> callout
- 输出 JSON summary
```

#### 其他 commands

- `commands/fold.md` → cortex-consolidate 周巩固
- `commands/doctor.md` → cortex-doctor 健康检查
- `commands/init.md` → cortex-install 初始化
- `commands/promote.md` → cortex-promote 晋级检测
- `commands/forget.md` → cortex-forget 遗忘扫描
- `commands/consolidate.md` → cortex-consolidate
- `commands/compact.md` → memory L4 压缩
- `commands/warden.md` → 腐化检测
- `commands/archive.md` → 归档执行
- `commands/update.md` → plugin update
- `commands/install_cron.md` → cron 注册

需参数的命令 (search / save / ingest / memory / recall) 仍建 command 让用户在 claude 内调, 但**不建 wrapper** (用户从 claude 调即可)。

### 2. plugin.json 注册

`plugins/tools/cortex/.claude-plugin/plugin.json` 加 commands 字段:
```json
"commands": [
  "./commands/lint.md",
  "./commands/dashboard.md",
  "./commands/fold.md",
  "./commands/doctor.md",
  "./commands/init.md",
  "./commands/promote.md",
  "./commands/forget.md",
  "./commands/consolidate.md",
  "./commands/compact.md",
  "./commands/warden.md",
  "./commands/archive.md",
  "./commands/update.md",
  "./commands/install_cron.md",
  "./commands/search.md",
  "./commands/save.md",
  "./commands/ingest.md",
  "./commands/memory.md",
  "./commands/recall.md",
  "./commands/refactor.md",
  "./commands/config.md"
]
```

### 3. wrapper 重写

`install_wrappers.sh` 生成 wrapper 模板:

```bash
#!/usr/bin/env bash
# <name>.sh — 跑 cortex /<name> command (无入参, 全权限)
set -euo pipefail

# 配置只读 (无 args)
CONFIG="$HOME/.cortex/config.json"
[[ -f "$CONFIG" ]] || { echo "✗ config 不存在, 跑 install.sh" >&2; exit 4; }

SETTINGS=$(jq -r '.settings // empty' "$CONFIG")
SETTINGS="${SETTINGS:-$HOME/.claude/settings.json}"

# 无限制启 claude, 调 slash command
exec claude --settings "$SETTINGS" -p "/cortex:<name>" --print
```

`--print` (非交互打印模式) + `-p` 用户提示。无 `--bare` 全权限。无 `--allowed-tools`。

wrapper 减为只调 command, 无内部 prompt 构建。

### 4. cron wrapper 同样

`scripts/cron/<name>.sh` 调用方式同, 但需保 flock + timeout + log。run.sh 仍存, 内部改 `claude -p "/cortex:<name>"`。

### 5. 删需参数的 wrapper

`~/.cortex/scripts/` 移除:
- search.sh / save.sh / ingest.sh / memory.sh / recall.sh / refactor.sh

保留:
- lint / fold / dashboard / doctor / init / promote / forget / consolidate / compact / warden / archive / update / install_cron / config (无参类)

总 wrapper 16 → ~15 (调整)。

或者: 全保留 wrapper, 但需参数类内部 hardcode 行为 (e.g. memory.sh 跑 "memory verify all"):
- search.sh: 跑 cortex-search 列最近 10 条
- save.sh: 跑 cortex-save 处理 inbox 全部
- ingest.sh: 跑 cortex-ingest 处理 inbox urls
- memory.sh: 跑 cortex-memory verify all
- recall.sh: 列高频 recall (top 10)
- refactor.sh: 列 refactor 建议

更友好: 保 16 wrapper, 各 hardcode 行为 (无入参可用)。

## 实施

### Step 1: 建 commands/ 目录 + 20 commands.md
### Step 2: plugin.json 注册
### Step 3: install_wrappers.sh 重写, 简化 wrapper 调 commands
### Step 4: cron 同样改
### Step 5: 真测 dashboard.sh

## 验收
- [ ] commands/ 含 20 commands
- [ ] plugin.json commands 字段全列
- [ ] wrapper 不接 args (跑 `lint.sh --check` 也无效)
- [ ] wrapper 调 `claude -p "/cortex:<name>"`
- [ ] wrapper 无 `--bare` / 无 `--allowed-tools`
- [ ] 真跑 `dashboard.sh` exit 0
- [ ] marketplace 同步
- [ ] 286 tests PASS

## 风险

| 风险 | 缓解 |
|------|------|
| claude 非 --bare 模式可能交互 | -p / --print 强制非交互 |
| 全权限工具 AI 误调危险 | AUTO_MODE strict + commands 内显式禁询问 |
| commands 不显示在 cortex plugin | plugin.json 注册 + reload |
| 测试 fixture 调用 wrapper 入参传 → 现失败 | 改 fixture |

## 子任务
单 trellis-implement (跨 commands/ 20 文件 + plugin.json + install_wrappers.sh + cron)。
