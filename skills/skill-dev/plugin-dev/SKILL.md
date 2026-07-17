---
name: plugin-dev
description: 创建与优化 Claude Code 插件的方法论框架。当用户要新建插件（搭 .claude-plugin/plugin.json manifest + 接线 commands/agents/skills/hooks/MCP + 挂 marketplace）、或审查优化现有插件（manifest 合规 / 组件接线完整性 / hook 健壮性 / marketplace 一致性）时使用。单组件（单个 skill / agent）编写或 9 维质量优化路由 skill-dev。仅手动 /plugin-dev 触发。
disable-model-invocation: true
argument-hint: "[create|optimize] <插件路径>"
arguments: "[create|optimize] <插件路径>"
---

# Plugin Dev — Claude Code 插件创建 / 优化方法论

> meta-skill：教如何搭建与打磨**整个 Claude Code 插件**（不是单个组件）。基于本仓库 `docs/plugin-development.md` + `plugins/tools/*` 7 个真实插件 + 官方规范。单组件级编写与 9 维评分优化归 [skill-dev]；本 skill 管**插件级**（manifest / 组件接线 / hook / marketplace）。

## 🔴 硬规（违反即失效）

1. **组件目录在插件根，禁进 `.claude-plugin/`** — `commands/` `agents/` `skills/` `hooks/` `scripts/` 必须在插件根；`.claude-plugin/` 只放 `plugin.json`。`SKILL.md` 文件名必须大写。
2. **manifest `name` 必填且 kebab-case** — `^[a-z0-9-]+$`；须与目录名、marketplace 条目 `name` 三者一致。
3. **接线双向核对** — `plugin.json` 的 `skills[]/agents[]/commands[]` 每条路径都要有真实文件；反过来每个组件文件都要被挂载。漏挂 = 组件不加载，悬挂 = 启动报错。
4. **hook / 脚本路径用 `${CLAUDE_PLUGIN_ROOT}`** — 禁写死绝对路径或相对 cwd；每个 hook 带 `timeout`，失败不得阻断会话。
5. **改任何 SKILL.md / agent.md / command.md 后过质量门**（项目 CLAUDE.md 强制）：
   ```bash
   claude -p "<待测内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
   端点抖动（400）时人工验 + 小步可回滚提交，标「待端点恢复补跑」。

## 路由（先判 create 还是 optimize）

| 输入信号 | 走 |
|---|---|
| 「新建插件 / 从零做个插件 / 搭插件脚手架」 | **流程 A · 创建** |
| 「优化 / 审查 / 检查这个插件 / 插件为什么不加载」 | **流程 B · 优化** |
| 只写单个 skill / agent / command | 🛑 停，路由 `/skill-dev`（本 skill 是插件级，不做单组件） |
| 单个 SKILL.md 纯质量评分 | 🛑 停，路由 `/skill-dev`（其流程 B 优化线做单 skill 深度评估） |

---

## 流程 A · 创建插件

1. **定范围（brainstorm，非凭空设计）** — 逐问用户：插件解决什么问题 / 目标用户 / 要哪些组件（command / agent / skill / hook / MCP）。关键分歧用 `AskUserQuestion` 拍板。
   🛑 **检查点1**：组件清单 + 每个组件一句话职责，给用户点头再搭。方向错晚改贵 100 倍。
2. **搭骨架** — 目录建在 `plugins/tools/<name>/`（对齐本仓库约定）：
   ```bash
   mkdir -p plugins/tools/<name>/.claude-plugin
   # 按清单只建需要的：commands/ agents/ skills/ hooks/ scripts/
   ```
3. **写 manifest** `plugins/tools/<name>/.claude-plugin/plugin.json`（字段以真实插件为准，`version` 本仓库多数省略）：
   ```jsonc
   {
     "name": "<name>",                    // 必填, kebab-case, = 目录名
     "description": "<一句话: 做什么 + 差异化核心>",
     "author": { "name": "...", "email": "...", "url": "..." },
     "homepage": "https://github.com/.../plugins/tools/<name>",
     "repository": "https://github.com/.../plugins/tools/<name>",
     "license": "AGPL-3.0-or-later",
     "keywords": ["...", "..."],
     "skills":   ["./skills/<name>-x"],   // 数组=逐条挂, 或字符串 "./skills/" 挂整目录
     "agents":   ["./agents/<name>-y.md"],
     "commands": ["./commands/<name>-z.md"],
     "hooks":    { /* 见下 */ },
     "userConfig": { /* 可选: 暴露给用户的配置项 */ }
   }
   ```
4. **写组件**（每个组件的具体写法委托 [skill-dev]，本 skill 只保证接线）：
   - command：`commands/*.md`，frontmatter `description` / `argument-hint` / `allowed-tools` / `model`；正文用 `$ARGUMENTS` / `$1`。
   - agent：`agents/*.md`，frontmatter `name`（必填）/ `description`（必填）/ `tools` / `model` / `skills`。
   - skill：`skills/<skill>/SKILL.md`（大写）。
   - hook：`plugin.json` 的 `hooks` 或独立 `hooks/hooks.json`；事件 `SessionStart`/`PreToolUse`/`PostToolUse`/`SubagentStart`/`UserPromptSubmit`/`Stop`…，`matcher` 如 `"Write|Edit"` / `"Bash(git:*)"` / `"*"`；`command` 用 `${CLAUDE_PLUGIN_ROOT}/scripts/x.sh` + `timeout`。
   - MCP：根 `.mcp.json` 的 `mcpServers`，密钥用 `${ENV_VAR}` 引用禁硬编码。
5. **本地验证**：
   ```bash
   jq . plugins/tools/<name>/.claude-plugin/plugin.json   # JSON 合法
   claude plugin add ./plugins/tools/<name>               # 装载, 或 /plugin install
   ```
   🛑 **检查点2**：逐个跑一遍 command / 触发 skill / 调 agent / 打 hook 事件，确认真加载再往下。
6. **挂 marketplace** — 在根 `.claude-plugin/marketplace.json` 的 `plugins[]` 追加条目（字段与真实条目一致，**无 version**）：
   ```jsonc
   { "name": "<name>", "source": "./plugins/tools/<name>",
     "description": "...", "author": {...},
     "homepage": "...", "repository": "...", "license": "...", "keywords": [...] }
   ```
7. **补文档 + 提交** — `README.md`（推荐）；变更自动 `git add`（项目规则），commit 遵 `feat(<name>): ...`，**禁 push**（等明确指令）。

---

## 流程 B · 优化插件（自带评分 rubric，不外包）

先跑机械体检定位硬伤，再按 rubric 打分排优先级，一轮修一类。

### 体检命令（先跑，硬伤优先）

```bash
P=plugins/tools/<name>
jq -e . $P/.claude-plugin/plugin.json >/dev/null || echo "❌ manifest JSON 非法"
jq -r '.name' $P/.claude-plugin/plugin.json | grep -qE '^[a-z0-9-]+$' || echo "❌ name 非 kebab-case"
# 接线双向: 挂载路径 vs 实际文件
for k in skills agents commands; do
  jq -r --arg k $k '.[$k][]? // empty' $P/.claude-plugin/plugin.json | while read p; do
    [ -e "$P/$p" ] || echo "❌ 悬挂: $k 挂了 $p 但文件不存在"; done
done
find $P/skills $P/agents $P/commands -maxdepth 2 \( -name SKILL.md -o -name '*.md' \) 2>/dev/null  # 反查漏挂
ls $P/skills/*/SKILL.md 2>/dev/null | grep -v '/SKILL.md$' && echo "❌ SKILL.md 命名错"
ls -d $P/.claude-plugin/commands $P/.claude-plugin/skills 2>/dev/null && echo "❌ 组件误放 .claude-plugin/ 内"
grep -rn 'command' $P/.claude-plugin/plugin.json | grep -q CLAUDE_PLUGIN_ROOT || echo "⚠️ hook 疑似写死路径"
```

### 评分 rubric（8 维，每维 1-10 × 权重，Σ/10 满分 100）

| # | 维度 | 权重 | 评分要点 |
|---|---|---|---|
| 1 | **Manifest 合规** | 16 | JSON 合法；`name` 必填 kebab-case；`description` 说清做什么+差异化；author/license/homepage 齐 |
| 2 | **组件接线完整** | 20 | `skills[]/agents[]/commands[]` 每条有真实文件（无悬挂）+ 每个文件被挂载（无漏挂）；路径大小写正确 |
| 3 | **结构规范** | 12 | 组件在插件根不在 `.claude-plugin/`；`SKILL.md` 大写；agent/command frontmatter 必填字段齐 |
| 4 | **Hook 健壮性** | 14 | `${CLAUDE_PLUGIN_ROOT}` 而非硬路径；每 hook 带 `timeout`；matcher 精确；失败不阻断会话；幂等 |
| 5 | **组件质量** | 14 | 逐个 skill/agent/command 过：触发词准、失败模式编码、无占位符残留（深评单 skill 另跑 `/skill-dev` 优化线，本维度只做门槛检查） |
| 6 | **Marketplace 一致性** | 12 | `marketplace.json` 条目 name/source/description/author/license/keywords 与 `plugin.json` 一致；source 路径存在 |
| 7 | **文档完整** | 6 | README 有装/用/例；CHANGELOG（如版本化）；description 无「灵活应用」空话尾巴 |
| 8 | **命名与元数据一致** | 6 | 目录名 = manifest name = marketplace name；keywords 命中真实能力非堆砌 |

**优化循环**：体检硬伤（维度 1/2/3 命中 = P0）先修 → 按最低维度一轮改一类 → 改后重跑体检 + 过质量门（硬规 5）→ 严格更好才留，否则 `git revert`。

---

## 失败模式（if-then 三段式：触发 → 一线修复 → 仍失败兜底）

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `claude plugin add` 装载失败 | `jq .` 验 manifest JSON + 查悬挂路径（体检命令） | 仍失败 → 逐组件二分：先只挂 skills 再逐个加，定位坏组件 |
| 组件不生效（命令/skill 不出现） | 查漏挂（文件存在但 `plugin.json` 没挂）+ 大小写 + `SKILL.md` 大写 | 仍不出 → 查是否误放 `.claude-plugin/` 内；重启会话重载 |
| hook 报错阻断会话 | 加 `timeout` + 改 `${CLAUDE_PLUGIN_ROOT}` 绝对引用 + 失败 `exit 0` 兜底 | 仍阻断 → 先从 manifest 摘掉该 hook 恢复可用，再单独调 |
| 质量门 `claude -p` 返 400/空 | 重试循环（端点抖动，见记忆 claude-p-endpoint-flaky） | 3 次仍败 → 人工审 + 小步可回滚提交，标「待端点恢复补跑」 |
| 优化后不确定是否更好 | 重跑体检对比硬伤数 + 过质量门 | 分数 fine-grained 不可信 → 破坏性/接线变更交用户确认，禁「我觉得更好」直落 |

## 反例（命中 = 流程错误）

- 组件塞进 `.claude-plugin/` 目录内（只该放 plugin.json）。
- 挂载路径与实际文件不符（悬挂 / 漏挂）却不做双向核对。
- hook `command` 写死绝对路径或漏 `timeout`，装到别人机器即崩。
- 凭空替用户设计插件功能（应 brainstorm 逐问）；纯文本代替 `AskUserQuestion`。
- 建完插件不挂 marketplace，或挂了但元数据与 plugin.json 不一致。
- 改 SKILL.md / agent.md 跳过 `claude -p` 质量门。
- 拿本 skill 去写单个 skill/agent 或做单 skill 评分（那是 skill-dev）。
- 自动 push（禁，等明确指令）。

## 资源

- 本仓库 `docs/plugin-development.md` — 结构 / 组件格式 / 发布流程详解。
- `plugins/tools/*`（skein / notify / version / cortex …）— 真实插件范例，manifest / hook / userConfig 抄这里。
- 根 `.claude-plugin/marketplace.json` — 市场条目真实字段模板。
- 官方：https://code.claude.com/docs/en/plugins · plugin-marketplaces · plugins-reference
