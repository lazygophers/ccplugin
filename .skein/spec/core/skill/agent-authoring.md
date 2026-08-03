---
title: agent-authoring
category: skill
keywords: [agent,documentation,structure,authoring,five-section,checkpoints]
status: active
inclusion: auto
---

## agent-authoring

## Agent 文档五段论结构

所有 skein agent 文档必须遵循如下统一结构 (5 个主要部分):

### 1. frontmatter + 一句话描述

- `name`: kebab-case 名称
- `description`: 一句话描述，包含主要职责
- `tools`, `model`, `effort`, `color`, `permissionMode`

### 2. 入参格式 (JSON)

规范的 JSON 模式说明，包含：
- `tid` / `sid` / `workdir`
- `mode` 或其他必要参数的枚举
- 例：`{"tid": "<id>", "sid": null, "workdir": "...", "mode": "sediment | amend | ..."}`

### 3. 工作流

有序步骤流程，包括：
- 第 0 步：开工钩子 (`skein-hooks agent-start`)
- 第 1～N 步：核心业务流程 (子命令/代码片段)
- 流程末尾：收工钩子 (`skein-hooks agent-stop`)
- 每步后可跟脚注说明 (采用 bullet 列表)

### 4. Checkpoints (🛑 开头)

列举本 agent 的所有关键要求与铁律，采用三段式 if-then：
- 禁止事项 (MUST NOT)
- 必做事项 (MUST)
- 公共铁律引用 (见 core/agent/skein-skill-agent-slim-01)

### 5. 返回数据格式 (JSON)

规范的 JSON schema，包含：
- 核心业务字段 (如 `written`, `archived`, `amended` 等)
- `tool_failures`: 工具失败列
- `needs_main`: 待人工介入的项
- 例：`{"mode": "...", "written": [...], "unfixed_links": [...]}`

### 6. 失败模式 (if-then 三段式)

表格格式列举：
| 触发 | 一线处理 | 兜底 |
- 每行代表一类失败场景的降级策略
- "一线处理" = 自动重试 / 修补
- "兜底" = 报错标记 + 人工介入

## 三类公共条目措辞

所有 agent 的 Checkpoints / 返回 / 失败模式中的相关措辞必须统一：

### 措辞 1：开工/收工钩子

**标准表述**: 
> 🛑 **开工/收工钩子必跑** — 钩子失败只记 note 不阻断本次作业; 无 hooks 配置时命令 no-op 立即返回。

### 措辞 2：工具失败标记

**标准表述**: 
> 🛑 **工具失败必标 `[工具失败: <原因>]`** — CLI 报错/超时禁把错误输出当结果返回 (main 消费错误摘要当有效数据 → 静默降级)。

### 措辞 3：公共铁律引用

**标准表述**: 
> 🛑 **公共铁律** (Recursion Guard + 无 AskUser + 无生命周期脚本) 见 core/agent/skein-skill-agent-slim-01。

## 枚举完整性检查

所有 mode/功能枚举 (入参格式、工作流标题、Checkpoints) 必须**全三角完整对应**：

- 入参格式的 mode 枚举 → 工作流中逐个有对应 `### N. mode名`
- 工作流的 mode 名 → 返回 JSON 的业务字段对应处理
- Checkpoints 中的 "工具失败" 情景 → 失败模式表中必有对应行

例：skein-specer 入参的 `mode` 为 `sediment | amend | reconstruct | maintain | prune | auto-fix`，则：
- 工作流中有 5 个对应小节 (### 1. sediment, ### 2. amend 等)
- 返回 JSON 有相应字段体现这 5 类结果 (written / amended / archived 等)

## 范例

参考现存 9 个 agent 的完整格式：
- skein-specer (五类写路径)
- skein-researcher (normal + bootstrap 双模式)
- skein-setup (fresh + trellis-migration)
- skein-executor
- skein-finisher
- skein-checker
- skein-clean
- skein-dedup
- skein-recaller
