---
name: plugin-dev
description: 创建与优化 Claude Code 插件的方法论框架。当用户要新建插件（搭 .claude-plugin/plugin.json manifest + 接线 commands/agents/skills/hooks/MCP/LSP/monitors + 挂 marketplace）、或审查优化现有插件（manifest 合规 / 组件接线完整性 / hook 健壮性 / marketplace 一致性）时使用。单组件（单个 skill / agent）编写或 9 维质量优化路由 skill-dev。仅手动 /plugin-dev 触发。
disable-model-invocation: true
argument-hint: "[create|optimize] <插件路径>"
arguments: "[create|optimize] <插件路径>"
---

# Plugin Dev — Claude Code 插件创建 / 优化方法论

> meta-skill：教如何搭建与打磨**整个 Claude Code 插件**（不是单个组件）。基于官方 plugins / plugins-reference / plugin-marketplaces 三篇规范 + 本仓库 `docs/` + `plugins/tools/*` 7 个真实插件。单组件级编写与 9 维评分优化归 [skill-dev]；本 skill 管**插件级**（manifest / 组件接线 / hook / 高级组件 / marketplace）。

细节分文件（按需读，禁全读）：
- [references/manifest-and-wiring.md](references/manifest-and-wiring.md) — plugin.json 全字段 + 组件目录 + namespace + version 语义
- [references/hooks.md](references/hooks.md) — 31 事件表 / 5 hook types / matcher / 退出码契约 / stdin payload / async / 路径变量
- [references/advanced-components.md](references/advanced-components.md) — MCP / LSP(+v2.1.205) / monitors / themes / channels / bin / settings / userConfig / dependencies
- [references/multi-language.md](references/multi-language.md) — 编译型陷阱 / 三方案 / 跨平台 / 共享代码
- [references/marketplace.md](references/marketplace.md) — marketplace.json schema / source 5 类型 / 发布流程
- [references/debugging.md](references/debugging.md) — claude --debug / validate --strict / plugin CLI 全集 / 错误信息速查 / hook/MCP/LSP/monitor 排查 / 版本解析 4 层 / 缓存+symlink
- [references/optimize-rubric.md](references/optimize-rubric.md) — 体检命令 / 8 维评分 / 优化循环

## 🔴 硬规（违反即失效）

1. **组件目录在插件根，禁进 `.claude-plugin/`** — `.claude-plugin/` 只放 `plugin.json`。`commands/ agents/ skills/ hooks/ scripts/ bin/ monitors/` 在插件根。`SKILL.md` 大写。插件根 ≠ `~/.claude/`。
2. **manifest `name` 必填且 kebab-case** — `^[a-z0-9-]+$`；须与目录名、marketplace 条目 `name` 三者一致。`name` 即 namespace 前缀（`/my-plugin:skill`）。
3. **接线双向核对** — `skills[]/agents[]/commands[]` 每条路径都要有真实文件；反过来每个组件文件都要被挂载。漏挂 = 静默不加载（最阴险），悬挂 = 启动报错。
4. **hook / 脚本路径用 `${CLAUDE_PLUGIN_ROOT}`** — 禁写死绝对路径或相对 cwd；每个 hook 带 `timeout`；失败 `exit 0` 兜底禁崩会话；guard 用 `exit 2`，**禁 `exit 1`**。
5. **密钥用 `${ENV_VAR}` 引用禁硬编码** — MCP `env` / 任何 secrets 一律环境变量。
6. **改任何 SKILL.md / agent.md / command.md 后过质量门**（项目 CLAUDE.md 强制）：
   ```bash
   claude -p "<待测内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
   ```
   端点抖动（400）时重试循环（见记忆 claude-p-endpoint-flaky）；3 次仍败 → 人工验 + 小步可回滚提交，标「待端点恢复补跑」。

## 路由（先判 create 还是 optimize）

| 输入信号 | 走 |
|---|---|
| 「新建插件 / 从零做个插件 / 搭插件脚手架」 | **流程 A · 创建** |
| 「优化 / 审查 / 检查这个插件 / 插件为什么不加载」 | **流程 B · 优化** |
| 只写单个 skill / agent / command | 🛑 停，路由 `/skill-dev`（本 skill 是插件级，不做单组件） |
| 单个 SKILL.md 纯质量评分 | 🛑 停，路由 `/skill-dev`（其流程 B 做单 skill 深度评估） |

---

## 流程 A · 创建插件

1. **定范围（brainstorm，非凭空设计）** — 逐问用户：插件解决什么问题 / 目标用户 / 要哪些组件（command / agent / skill / hook / MCP / LSP / monitor）。关键分歧用 `AskUserQuestion` 拍板。
   🛑 **检查点1**：组件清单 + 每个组件一句话职责，给用户点头再搭。方向错晚改贵 100 倍。
2. **搭骨架** — 目录建在 `plugins/tools/<name>/`（对齐本仓库约定）：
   ```bash
   mkdir -p plugins/tools/<name>/.claude-plugin
   # 按清单只建需要的：commands/ agents/ skills/ hooks/ scripts/ bin/ monitors/
   ```
   单 skill 插件可省 `skills/`，`SKILL.md` 直接放根。
3. **写 manifest** `.claude-plugin/plugin.json`（全字段 + namespace + version 语义见 [references/manifest-and-wiring.md](references/manifest-and-wiring.md)）：
   ```jsonc
   {
     "name": "<name>",                    // 必填, kebab-case, = 目录名, = namespace 前缀
     "description": "<做什么 + 差异化核心>",
     "author": { "name": "...", "email": "...", "url": "..." },
     "homepage": "...", "repository": "...", "license": "AGPL-3.0-or-later",
     "keywords": ["..."],
     "skills":   ["./skills/<name>-x"],   // 数组=逐条挂, 或 "./skills/" 挂整目录
     "agents":   ["./agents/<name>-y.md"],
     "commands": ["./commands/<name>-z.md"],
     "hooks":    { /* 见 references/hooks.md */ },
     "userConfig": { /* 可选, 见 references/advanced-components.md */ }
     // version 省略则走 git commit SHA；正式发布再加 semver
   }
   ```
4. **写组件**（每个组件的具体写法委托 `/skill-dev`，本 skill 只保证接线）：
   - **command**：`commands/*.md`，frontmatter `description` / `argument-hint` / `allowed-tools` / `model`；正文用 `$ARGUMENTS` / `$1`。
   - **agent**：`agents/*.md`，frontmatter `name`（必填）/ `description`（必填）/ `tools` / `model` / `skills`。
   - **skill**：`skills/<skill>/SKILL.md`（大写）。
   - **hook**：`plugin.json` 内联 `hooks` 或独立 `hooks/hooks.json`；事件 / matcher / 退出码 / payload / async / timeout **必读** [references/hooks.md](references/hooks.md)。
   - **MCP / LSP / monitor / bin / settings / userConfig / outputStyles**：见 [references/advanced-components.md](references/advanced-components.md)。
   - **脚本分发**（编译型/解释型/uvx）：见 [references/multi-language.md](references/multi-language.md)。🔴 核心：`claude plugin add` 不编译不装依赖。
5. **本地验证**：
   ```bash
   jq . plugins/tools/<name>/.claude-plugin/plugin.json   # JSON 合法
   claude plugin validate                                  # 官方校验（提交前必跑）
   claude --plugin-dir ./plugins/tools/<name>              # 开发加载（非安装）
   # 进会话后 /reload-plugins 重载改后生效
   ```
   🛑 **检查点2**：逐个跑一遍 command / 触发 skill（`/<name>:<skill>`）/ 调 agent / 打 hook 事件，确认真加载再往下。
6. **挂 marketplace** — 在仓库根 `.claude-plugin/marketplace.json` 的 `plugins[]` 追加条目（全 schema + source 5 类型见 [references/marketplace.md](references/marketplace.md)）：
   ```jsonc
   { "name": "<name>", "source": "./plugins/tools/<name>",
     "description": "...", "author": {...},
     "homepage": "...", "repository": "...", "license": "...", "keywords": [...] }
   ```
7. **补文档 + 提交** — `README.md`（推荐）；变更自动 `git add`（项目规则），commit 遵 `feat(<name>): ...`，**禁 push**（等明确指令）。

---

## 流程 B · 优化插件

先跑机械体检定位硬伤，再按 8 维 rubric 打分排优先级，一轮修一类。**体检命令 + 完整 rubric 见 [references/optimize-rubric.md](references/optimize-rubric.md)。**

8 维速览（权重）：① Manifest 合规(16) ② 组件接线完整(20) ③ 结构规范(12) ④ Hook 健壮性(14) ⑤ 组件质量(14, 深评交 `/skill-dev`) ⑥ Marketplace 一致性(12) ⑦ 文档完整(6) ⑧ 命名元数据一致(6)。

**优化循环**：体检硬伤（维度 1/2/3 命中 = P0 先修）→ 按最低维度一轮改一类（单变量轮）→ 改后重跑体检 + 过质量门（硬规 6）→ 严格更好才留否则 `git revert` → 触顶（连续 2 轮 Δ<2）break。

---

## 失败模式速查（触发 → 一线修复 → 仍失败兜底）

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `claude plugin add` / `--plugin-dir` 装载失败 | `jq .` 验 manifest JSON + 体检查悬挂（见 optimize-rubric.md）| 逐组件二分：先只挂 skills 再逐个加，定位坏组件 |
| 组件不生效（命令/skill 不出现）| 查漏挂（文件存在但 manifest 没挂）+ 大小写 + `SKILL.md` 大写；注意调用名是 `/<plugin>:<skill>` | 查是否误放 `.claude-plugin/` 内；`/reload-plugins` 或重启会话重载 |
| hook 报错阻断会话 | 加 `timeout` + 改 `${CLAUDE_PLUGIN_ROOT}` + 失败 `exit 0` 兜底；guard 用 `exit 2` 禁 `exit 1` | 先从 manifest 摘掉该 hook 恢复可用，再单独调 |
| hook 不触发 | 查 matcher 拼写（大小写敏感）/ event 名（`PostToolUse` 非 `post_tool_use`）/ command 路径 / 脚本 `+x` | `claude --debug` 看触发实况 |
| marketplace source relative 失效 | 用户从 URL 加 marketplace 时 relative 不解析 → 改 github/url/npm source | git/本地加 marketplace 才用 relative |
| 质量门 `claude -p` 返 400/空 | 重试循环（端点抖动，记忆 claude-p-endpoint-flaky）| 3 次仍败 → 人工审 + 小步可回滚提交，标「待端点恢复补跑」|
| 优化后不确定是否更好 | 重跑体检对比硬伤数 + 过质量门 | 分数 fine-grained 不可信 → 破坏性/接线变更交用户确认，禁「我觉得更好」直落 |

## 反例（命中 = 流程错误）

- 组件塞进 `.claude-plugin/` 目录内（只该放 plugin.json）。
- 挂载路径与实际文件不符（悬挂 / 漏挂）却不做双向核对。
- hook `command` 写死绝对路径或漏 `timeout`，装到别人机器即崩。
- guard hook 用 `exit 1`（语义模糊）或崩在非法 JSON stdin（会卡死会话）。
- MCP `env` / 任何 secrets 硬编码（应 `${ENV_VAR}`）。
- 凭空替用户设计插件功能（应 brainstorm 逐问）；纯文本代替 `AskUserQuestion`。
- 建完插件不挂 marketplace，或挂了但元数据与 plugin.json 不一致。
- 只放 `.go`/`.rs` 源码不预编译（`claude plugin add` 不编译，用户机器跑不起来）。
- 改 SKILL.md / agent.md 跳过 `claude -p` 质量门。
- 拿本 skill 去写单个 skill/agent 或做单 skill 评分（那是 skill-dev）。
- 自动 push（禁，等明确指令）。

## 资源

- **官方三篇**：[plugins](https://code.claude.com/docs/en/plugins) · [plugins-reference](https://code.claude.com/docs/en/plugins-reference) · [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- 本仓库 `docs/plugin-development.md` — 结构 / 组件格式 / 发布流程教程。
- 本仓库 `docs/api-reference.md` — manifest / hooks / MCP / marketplace 完整 schema。
- 本仓库 `docs/supported-languages.md` + `compiled-languages-guide.md` — 多语言 / 编译型指南。
- 本仓库 `docs/best-practices.md` — 设计原则 / 命名 / 安全。
- `plugins/tools/*`（skein / notify / version / cortex / deepresearch / novelist / trellisx）— 真实插件范例，manifest / hook / userConfig / pyproject 抄这里。
- 根 `.claude-plugin/marketplace.json` — 市场条目真实字段模板。

## 诚实边界

- 覆盖 Claude Code 插件系统（官方规范截至 2026-07-17 fetch）；部分新字段标注 `{/* min-version: x.y.z */}` 依赖用户 Claude Code 版本。
- 组件深度质量评估（skill 9 维评分 / agent body 设计）路由 `/skill-dev`，本 skill 维度 5 只做门槛检查。
- 调研来源：官方文档（一手）+ 本仓库 docs + 真实插件实证；无第三方基准。评分 rubric 权重为经验汇总，fine-grained 不可信，重要决策人审。
