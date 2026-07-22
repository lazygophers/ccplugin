---
name: plugin-dev
description: '创建与优化 Claude Code 插件的方法论框架。流程 A 新建 (plugin.json manifest + 接线 commands/agents/skills/hooks/MCP/LSP + 挂 marketplace)，流程 B 优化现有 (8 维: manifest 合规/接线完整/hook 健壮/marketplace 一致)。单组件路由 /skill-dev。仅手动 /plugin-dev。'
disable-model-invocation: true
argument-hint: "[create|optimize] <插件路径>"
arguments: "[create|optimize] <插件路径>"
---

# Plugin Dev — Claude Code 插件创建 / 优化方法论

教如何搭建与打磨**整个 Claude Code 插件**（manifest / 组件接线 / hook / 高级组件 / marketplace）。单组件级编写与评分优化归 `/skill-dev`；本 skill 管**插件级**。基于官方 plugins / plugins-reference / plugin-marketplaces 三篇规范 + 本仓库 `docs/` + `plugins/tools/*` 真实插件。

细节分文件（按需读，禁全读）：
- [references/manifest-and-wiring.md](references/manifest-and-wiring.md) — plugin.json 全字段 + 组件目录 + namespace + version 语义
- [references/hooks.md](references/hooks.md) — 31 事件表 / 5 hook types / matcher / 退出码契约 / stdin payload / async / 路径变量
- [references/advanced-components.md](references/advanced-components.md) — MCP / LSP(+v2.1.205) / monitors / themes / channels / bin / settings / userConfig / dependencies
- [references/multi-language.md](references/multi-language.md) — 编译型陷阱 / 三方案 / 跨平台 / 共享代码
- [references/marketplace.md](references/marketplace.md) — marketplace.json schema / source 5 类型 / 发布流程
- [references/debugging.md](references/debugging.md) — claude --debug / validate --strict / plugin CLI 全集 / 错误信息速查 / hook/MCP/LSP/monitor 排查 / 版本解析 4 层 / 缓存+symlink
- [references/optimize-rubric.md](references/optimize-rubric.md) — 体检命令 / 8 维评分 (方向轴+理想值+底线) / validation-gate 循环

## 硬护栏（无法正向表述的禁令，配正例）

| 禁 (elephant) | 正例 (target) |
|---|---|
| 组件塞进 `.claude-plugin/` 目录 | 组件在插件根；`.claude-plugin/` 仅放 `plugin.json` |
| hook `command` 写死绝对路径 / 漏 `timeout` | `${CLAUDE_PLUGIN_ROOT}/scripts/x.sh` + 每 hook 带 `timeout` |
| guard hook `exit 1`（语义模糊）| guard 用 `exit 2` 阻断；副作用 hook 失败 `exit 0` 兜底 |
| MCP `env` / secrets 硬编码 | `${ENV_VAR}` 引用环境变量 |
| 凭空替用户设计插件功能 / 纯文本代替 `AskUserQuestion` | brainstorm 逐问 + 关键分歧用 `AskUserQuestion` 拍板 |
| 自动 push | 改完 `git add`（项目规则）+ commit，**禁 push** 等明确指令 |
| 改 SKILL.md / agent.md 跳过质量门 | 改完过 `claude -p` 质量门（项目 CLAUDE.md 强制）|

质量门命令（端点抖动 400 时重试循环 8 次，见记忆 claude-p-endpoint-flaky；仍败 → 人工验 + 小步可回滚提交，标「待端点恢复补跑」）：

```bash
claude -p "<待测内容>" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

## 路由（先判 create 还是 optimize）

| 输入信号 | 走 |
|---|---|
| 「新建插件 / 从零做个插件 / 搭插件脚手架」 | **流程 A · 创建** |
| 「优化 / 审查 / 检查这个插件 / 插件为什么不加载」 | **流程 B · 优化** |
| 只写单个 skill / agent / command | 🛑 停，路由 `/skill-dev`（本 skill 是插件级，不做单组件） |
| 单个 SKILL.md 纯质量评分 | 🛑 停，路由 `/skill-dev`（其流程 B 做单 skill 深度评估） |

---

## 流程 A · 创建插件

一句话职责：搭一个**装得上、加载得了、接线零悬挂**的插件骨架，深度质量交 `/skill-dev`。

### 1. 定范围（brainstorm，非凭空设计）
逐问用户：插件解决什么问题 / 目标用户 / 要哪些组件（command / agent / skill / hook / MCP / LSP / monitor）。关键分歧用 `AskUserQuestion` 拍板。

**Done when:** 组件清单 + 每个组件一句话职责，用户点头（用 `AskUserQuestion`，禁纯文本）。

### 2. 搭骨架
目录建在 `plugins/tools/<name>/`（对齐本仓库约定）：
```bash
mkdir -p plugins/tools/<name>/.claude-plugin
# 按清单只建需要的：commands/ agents/ skills/ hooks/ scripts/ bin/ monitors/
```
单 skill 插件可省 `skills/`，`SKILL.md` 直接放根。

**Done when:** 清单中每个组件目录都已创建，无多余空目录。

### 3. 写 manifest
`.claude-plugin/plugin.json`（全字段 + namespace + version 语义见 [references/manifest-and-wiring.md](references/manifest-and-wiring.md)）：
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

**Done when:** `jq .` 通过；`name` kebab-case = 目录名；`description` 含「做什么 + 差异化」。

### 4. 写组件
每个组件的具体写法委托 `/skill-dev`，本 skill 只保证接线。

**传递要求：目标插件组件默认正向表述，仅必要硬护栏场景保留反例（命名被拒模式 + 原因 + 正例）。** 组件（command / agent / skill 正文）写成「该做什么」而非「别做什么」。

- **command**：`commands/*.md`，frontmatter `description` / `argument-hint` / `allowed-tools` / `model`；正文用 `$ARGUMENTS` / `$1`。
- **agent**：`agents/*.md`，frontmatter `name`（必填）/ `description`（必填）/ `tools` / `model` / `skills`。
- **skill**：`skills/<skill>/SKILL.md`（大写）。
- **hook**：`plugin.json` 内联 `hooks` 或独立 `hooks/hooks.json`；事件 / matcher / 退出码 / payload / async / timeout **必读** [references/hooks.md](references/hooks.md)。
- **MCP / LSP / monitor / bin / settings / userConfig / outputStyles**：见 [references/advanced-components.md](references/advanced-components.md)。
- **脚本分发**（编译型/解释型/uvx）：见 [references/multi-language.md](references/multi-language.md)。🔴 核心：`claude plugin add` 不编译不装依赖。

**Done when:** 体检 #3 #4 零悬挂零漏挂（挂载路径都有真实文件 + 每个组件文件都被挂载）。

### 5. 本地验证
```bash
jq . plugins/tools/<name>/.claude-plugin/plugin.json   # JSON 合法
claude plugin validate                                  # 官方校验（提交前必跑）
claude --plugin-dir ./plugins/tools/<name>              # 开发加载（非安装）
# 进会话后 /reload-plugins 重载改后生效
```

**Done when:** 逐个跑一遍 command / 触发 skill（`/<name>:<skill>`）/ 调 agent / 打 hook 事件，确认真加载（观察到实际触发，非「应该能跑」）。

### 6. 挂 marketplace
在仓库根 `.claude-plugin/marketplace.json` 的 `plugins[]` 追加条目（全 schema + source 5 类型见 [references/marketplace.md](references/marketplace.md)）：
```jsonc
{ "name": "<name>", "source": "./plugins/tools/<name>",
  "description": "...", "author": {...},
  "homepage": "...", "repository": "...", "license": "...", "keywords": [...] }
```

**Done when:** `marketplace.json` 条目 name/source/description/author/license/keywords 与 `plugin.json` 逐字段对齐。

### 7. 补文档 + 提交
`README.md`（推荐）；变更自动 `git add`（项目规则），commit 遵 `feat(<name>): ...`，**禁 push**。

**Done when:** 填完下面的创建报告交用户。

<plugin-creation-report-template>
## 插件创建报告 · <name>

### 范围
- 解决的问题：<一句话>
- 目标用户：<一句话>
- 关键分歧裁决（`AskUserQuestion`）：<列表>

### 组件清单
| 组件 | 路径 | 一句话职责 |
|---|---|---|
| command | commands/<x>.md | ... |
| skill | skills/<y>/SKILL.md | ... |
| agent | agents/<z>.md | ... |
| hook | hooks/... | ... |

### Manifest
- name：<kebab-case> (= 目录名 ✓)
- description 含「做什么 + 差异化」：✓ / ✗
- 字段齐 (author/license/homepage)：✓ / ✗

### 接线表（双向核对）
- 悬挂（挂了无文件）：无 / <列表>
- 漏挂（文件没挂）：无 / <列表>

### 验证结果
- `jq .`：✓ / ✗
- `claude plugin validate`：✓ / ✗
- `--plugin-dir` 实测加载 + 逐组件触发：✓ / ✗
- marketplace 条目逐字段对齐：✓ / ✗
- 质量门 `claude -p`（改了 .md 才跑）：✓ / 待端点恢复补跑
</plugin-creation-report-template>

---

## 流程 B · 优化插件

一句话职责：先机械体检定位硬伤，再按 8 维 rubric 打分排优先级，validation-gate 循环收敛到触顶。**体检命令 + 完整 rubric 见 [references/optimize-rubric.md](references/optimize-rubric.md)。**

8 维速览（权重）：① Manifest 合规(16) ② 组件接线完整(20) ③ 结构规范(12) ④ Hook 健壮性(14) ⑤ 组件质量(14, 深评交 `/skill-dev`) ⑥ Marketplace 一致性(12) ⑦ 文档完整(6) ⑧ 命名元数据一致(6)。

### B-1. 体检硬伤先修
跑 [optimize-rubric.md](references/optimize-rubric.md) 体检命令 9 项。维度 1/2/3 命中（JSON 非法 / 悬挂漏挂 / 组件误放）= P0，先修。

**Done when:** 体检 9 项全绿或仅剩非阻断 ⚠️。

### B-2. 按 8 维打分 + 排优先级
按 rubric 每维 1-10 × 权重打分；记 before 分 + 方向轴 + 完成准则底线状态。**独立验证**：spawn 独立子 agent 跑评分（禁同 context 自评，自评 +1 偏乐观）。

**Done when:** 8 维 before 分齐全，最低维度（且方向轴未达标）锁定为本轮目标。

**传递要求：本轮若改组件正文（skill/agent/command body），目标组件默认正向表述，仅必要硬护栏场景保留反例（命名被拒模式 + 原因 + 正例）。**

### B-3. validation-gate 循环（6 要素缺一不可）

1. **单变量轮** — 一轮改一维度（或一相关簇：2/3/4 接线）。
2. **二层 gate 通过才留**：
   - **gross gate**：总分 Δ>0（体检硬伤数↓ + 接线零悬挂漏挂 + 质量门非空）。
   - **人审 gate**：破坏性/接线/触发词变更 → `AskUserQuestion` 交用户确认，禁「我觉得更好」直落。
   - **方向轴校验**：退步维度（方向轴反向走）即使总分涨也标警示，留滚交人审。
3. **ratchet 回滚** — 不通过 `git revert HEAD`（禁 `git reset --hard`，保留历史可审计）。
4. **触顶停** — 连续 2 轮 Δ<2 → break。
5. **膨胀护栏** — 改后体积 > 原×1.5 → 拒提交（优化 ≠ 膨胀，删 > 增）。
6. **独立验证** — 每轮评分 spawn 独立子 agent，禁同 context 自评。

**Done when:** 触顶 break 或所有维度达完成准则底线；填完下面的优化报告交用户。

<plugin-optimization-report-template>
## 插件优化报告 · <name>

### 体检结果
- 硬伤（P0，维度 1/2/3）：<列表或无>
- ⚠️ 非阻断：<列表或无>

### 8 维 before → after + Δ + 方向轴
| # | 维度 | 权重 | 方向 | 理想值 | before | after | Δ | 完成底线达 ✓/✗ |
|---|---|---|---|---|---|---|---|---|
| 1 | Manifest 合规 | 16 | ↑ | 10 | | | | |
| 2 | 组件接线完整 | 20 | ↑ | 10 | | | | |
| 3 | 结构规范 | 12 | ↑ | 10 | | | | |
| 4 | Hook 健壮性 | 14 | ↑ | 10 | | | | |
| 5 | 组件质量 | 14 | ↑ | 8 | | | | |
| 6 | Marketplace 一致 | 12 | ↑ | 10 | | | | |
| 7 | 文档完整 | 6 | ↑ | 8 | | | | |
| 8 | 命名元数据一致 | 6 | ↑ | 10 | | | | |
| **Σ/100** | | | | | | | | |

### 留 / 滚清单
| 轮次 | 维度 | gross Δ | 方向轴 | gate (gross+人审) | 留/滚 | 原因 |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

### 触顶信号
- 连续 Δ<2 轮数：<n> / 是否 break：是 / 否
- 膨胀护栏：改后体积 / 原体积 = <比> (≤1.5 ✓ / >1.5 拒提交)
- 独立验证：每轮 spawn 子 agent ✓ / 同 context 自评 ✗

### 未达底线维度（交后续轮或 `/skill-dev` 深评）
- <列表或全达>
</plugin-optimization-report-template>

### 可视化成果卡片（可选，展示战绩）

复制 `templates/result-card.html`，填插件名 / before-after-Δ 加权分 / 体检 P0 硬伤 / 8 维 before▸after / 爬山轮次 / 改进摘要 / 日期，浏览器打开或截图。模板自带 3 风格（swiss/terminal/newspaper，URL hash 切换），8 维加权（权重 ×16/20/12/14/14/12/6/6 = 100），JS 自动算加权分与条宽，无需外部脚本。

---

## Failure modes（特征性失误 → 修复）

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| `claude plugin add` / `--plugin-dir` 装载失败 | `jq .` 验 manifest JSON + 体检查悬挂 | 逐组件二分：先只挂 skills 再逐个加，定位坏组件 |
| 组件不生效（命令/skill 不出现）| 查漏挂 + 大小写 + `SKILL.md` 大写；调用名是 `/<plugin>:<skill>` | 查是否误放 `.claude-plugin/` 内；`/reload-plugins` 或重启会话 |
| hook 报错阻断会话 | 加 `timeout` + 改 `${CLAUDE_PLUGIN_ROOT}` + 失败 `exit 0`；guard 用 `exit 2` | 先从 manifest 摘掉该 hook 恢复可用，再单独调 |
| hook 不触发 | 查 matcher 拼写（大小写敏感）/ event 名（`PostToolUse` 非 `post_tool_use`）/ command 路径 / 脚本 `+x` | `claude --debug` 看触发实况 |
| marketplace source relative 失效 | 用户从 URL 加 marketplace 时 relative 不解析 → 改 github/url/npm source | git/本地加 marketplace 才用 relative |
| 质量门 `claude -p` 返 400/空 | 重试循环 8 次（端点抖动） | 仍败 → 人工审 + 小步可回滚提交，标「待端点恢复补跑」|
| 优化后不确定是否更好 | 独立子 agent 重跑体检对比 + 过质量门 | 分数 fine-grained 不可信 → 破坏性/接线变更交用户确认 |

## Rejected framings（被拒命名/框法 + 原因 + 正例）

- **「`exit 1` 作 guard 阻断」** — 语义模糊（既非成功也非阻断），Claude Code 不识别为 guard。正例：guard 用 `exit 2`；副作用 hook 失败 `exit 0` 兜底。
- **「组件放 `.claude-plugin/` 内整齐」** — `.claude-plugin/` 是 manifest 专用，放组件会被忽略。正例：组件在插件根，`.claude-plugin/` 仅 `plugin.json`。
- **「hook 写绝对路径便于定位」** — 装到别人机器即崩。正例：`${CLAUDE_PLUGIN_ROOT}/scripts/x.sh`。
- **「`claude plugin add` 会帮我编译/装依赖」** — add 只拷贝不构建。正例：预编译二进制入 bin/，或 uvx/解释型分发，见 multi-language.md。
- **「建完插件不挂 marketplace 也能用」** — 不挂则无法被市场发现/安装。正例：追加 `marketplace.json` 条目并逐字段对齐。
- **「拿本 skill 写单个 skill/agent」** — 越界，单组件归 `/skill-dev`。正例：路由 `/skill-dev`。

## 资源

- **官方三篇**：[plugins](https://code.claude.com/docs/en/plugins) · [plugins-reference](https://code.claude.com/docs/en/plugins-reference) · [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- 本仓库 `docs/plugin-development.md` — 结构 / 组件格式 / 发布流程教程。
- manifest / hooks / MCP / marketplace 完整 schema 见官方 [plugins-reference](https://code.claude.com/docs/en/plugins-reference)；多语言 / 编译型分发见 references/multi-language.md；设计原则 / 命名 / 安全见官方 [plugins](https://code.claude.com/docs/en/plugins)。
- `plugins/tools/*`（skein / notify / version / cortex / deepresearch / novelist / trellisx）— 真实插件范例。
- 根 `.claude-plugin/marketplace.json` — 市场条目真实字段模板。

## Out of scope

- 覆盖 Claude Code 插件系统（官方规范截至 2026-07-17 fetch）；部分新字段标 `{/* min-version: x.y.z */}` 依赖用户 Claude Code 版本。
- 组件深度质量评估（skill 9 维评分 / agent body 设计）路由 `/skill-dev`，本 skill 维度 5 只做门槛检查。
- 评分 rubric 权重为经验汇总，fine-grained 不可信，重要决策人审。
