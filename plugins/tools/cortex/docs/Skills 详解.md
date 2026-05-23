# Skills 详解

cortex 提供 **19 个 skill** (PR1-4 整改 21→13, 后续新增 cortex-config + cortex-image + 多模态理解三件套 + cortex-dataview 六件至 19)。skill 由 description 池语义匹配自动触发, 也可显式调用 (`/cortex:<相关 command>`)。

全部 skill 遵循渐进披露: 入口 SKILL.md ≤ 80 行 (frontmatter + 触发词 + 决策树 + AUTO_MODE 分支 + references 指针表), 细节迁 `references/<topic>.md` 按需加载。

## 整改 (PR1-4) 摘要

- **删 7 skill**: cortex-new, cortex-canvas, cortex-reflect, cortex-ingest-bulk, cortex-schema, cortex-locale, cortex-forget (forget skill 删, slash + wrapper 保 → AI 加载 cortex-memory 走 forget 子流程)
- **合 1 skill**: cortex-recall → cortex-search/references/memory-recall.md
- **拆 6 大 skill**: dashboard / install / save / lint / search / refactor / digest / ingest 全部多文件渐进披露

## 触发模型

| 触发方式 | 说明 |
|----------|------|
| 自动 (自然语言命中 description Triggers) | search / save / ingest / lint / memory / digest / promote / session |
| 显式 (`disable-model-invocation: true`) | install / dashboard / doctor / refactor / html |

显式 skill 必须用户明确请求, 防止误触发副作用 (写 vault 骨架 / 大批量改盘等)。

## 15 个 Skill 速查

**范围标记**: 全局 (用户/系统级) · 当前目录 (PWD) · 知识库 (vault) · 记忆层 (`记忆/L0-L4`)

| Skill | 范围 | 触发 | 用途 | 类型 |
|-------|-----|------|------|------|
| `cortex-install` | 全局+知识库 | "安装 cortex" / "init vault" | 创建 vault 骨架 + 默认模板 + 配置 + cron + locale 子流程 | 显式 |
| `cortex-doctor` | 全局+知识库 | "vault 健康吗" / "doctor" | 体检 vault + 依赖 + 配置 + schema 校验子流程 | 显式 |
| `cortex-save` | 知识库 | "落档 X" / "save this" | 写新笔记 (frontmatter + block-id, 含 new 子流程) | 自动 |
| `cortex-ingest` | 当前目录+知识库 | "ingest <url>" / "深度分析当前目录" | URL / 文件 / git repo / 项目目录 → 知识库 (含 bulk 子流程) | 自动 |
| `cortex-search` | 知识库+记忆层 | "搜知识库 X" / "想起 X" / "回忆" | MCP 4 级 + vault + 记忆层语义搜索 (recall 合入) | 自动 |
| `cortex-memory` | 记忆层 | "整理记忆" / "维护记忆" / "查我的记忆" / "忘了 X" | 默认: 维护扫 5 阶段 (整理 / 升级候选 / 补充 / forget 标记 / 评分); 有 verb: URI CRUD (read/write/update/delete) | 自动 |
| `cortex-promote` | 记忆层 | "升级记忆" | L2 → L1 / L1 → L0 (经用户审批) | 自动 |
| `cortex-digest` | 记忆层+知识库 | "digest" / "巩固记忆" / "consolidate" | 8 阶段全量深度 (read/analyze/process/maintain/consolidate/enrich/verify/cleanup), `.cortex/state/*.json` 增量游标 | 自动 |
| `cortex-session` | 知识库 | "导入 session" | jsonl transcript → 知识库 sessions/ | 显式 |
| `cortex-lint` | 知识库 | "vault 体检" / "lint" | 跑 30 条规则 + autofix 循环修复 | 自动 |
| `cortex-refactor` | 知识库 | "改名" / "合并 / 拆分" / "evolution-apply" | 改名 / 合并 / 拆分页面 + 同步 wikilink + canvas 子流程 | 显式 |
| `cortex-dashboard` | 知识库 | "刷新仪表盘" | 重渲 index.md / hot.md / canvas | 显式 |
| `cortex-html` | 知识库 | "渲染 HTML 卡片" | 把 frontmatter / 数据渲染为 inline HTML | 显式 |
| `cortex-config` | 全局+知识库 | "查看 cortex 配置" / "改 cortex 配置" | 展示/编辑 `~/.cortex/config.json` + vault `.cortex/config/*.yaml`; Stop hook 校验 schema | 自动 |
| `cortex-image` | 知识库 | "生成图" / "做张图" / "AI 画图" | 文生图 — 多 provider 配置 (`.cortex/config/image-gen.yaml`) 随机/指定; 10 风格 + 6 排版库; Junior Designer 工作流 | 自动 |
| `cortex-image-understand` | 知识库 | "看图" / "识图" / "VQA" / "OCR" / "图里写了什么" | 图理解 — 多 provider VLM (`.cortex/config/image-understand.yaml`); describe/ask/extract/OCR 四模式 | 自动 |
| `cortex-video-understand` | 知识库 | "看视频" / "视频理解" / "总结视频" | 视频理解 — 多 provider; video_url + frames (ffmpeg) 双模式; describe/ask/extract | 自动 |
| `cortex-audio-understand` | 知识库 | "转录" / "听音频" / "ASR" / "音频问答" | 音频理解 — asr (Whisper/GLM-ASR multipart) + chat (gpt-4o-audio/qwen-audio); transcribe/describe/ask | 自动 |
| `cortex-dataview` | 知识库 | "dataview" / "DQL" / "查询块" / "dv.pages" | Dataview 块构建/修改/解释; 5 references; marker 幂等改写; AUTO_MODE 拒 dataviewjs | 自动 |

## 行为约束 (AUTO_MODE persistent, 所有 skill 一致)

shell wrapper / slash command 触发时:

- **禁询问**: AskUserQuestion 工具不可用
- **禁中止**: 报状态后停 = 违规, 必须循环修复直至稳定 或 工具客观失败 (磁盘只读 / 权限拒绝 / git lock)
- **禁推卸**: "需人工" / "AI 不会" / "建议后续处理" 等推卸辞令禁止输出
- **自决执行**: 遇歧义按推荐默认值执行; 工具不熟悉则尝试其他组合 (Bash / Edit / Write / MCP / WebSearch / Read 现有样本)

IDE 内交互模式不受此约束, 可走 `AskUserQuestion` 4 选项流程。

## Skill 详细文档

每个 skill 的完整描述 / 触发短语 / 失败处理见 `skills/<name>/SKILL.md`。

## SKILL.md + references/ 架构 (P5 引入)

借鉴 [agent-playbook context-layering](https://github.com/zhaono1/agent-playbook/blob/main/docs/context-layering-for-agent-playbooks.md) 3 层模型:

- **L1 always-on**: AGENT.md 协作约定 + hook 注入 (每会话加载)
- **L2 routing**: SKILL.md procedural (skill 触发时加载, 留骨架 + 指针)
- **L3 on-demand**: `skills/<name>/references/*.md` (按需查阅, 不进默认 context)

### 已拆分 references 的 skill

| Skill | SKILL.md 行数 | references/ 文件 |
|---|---|---|
| cortex-ingest | ~200 (原 497) | layout.md / extract.md / exclude.md / knowledge-graph.md |
| cortex-digest | ~140 (原 175) | extraction.md / cleanup.md / evolution.md |

### lint 强制 (rule skill-references-exists)

SKILL.md / AGENT.md / `agents/*.md` 内 `[xxx](references/<name>.md)` 链接的目标必须存在, 否则 lint 报 warn。autofix=false (需手工修复或挪 reference)。

## cortex-digest evolution 抽取 (P5)

cortex-digest 8 阶段第 8a 阶段做 evolution 抽取, 借鉴 [self-improving-agent multi-memory](https://github.com/zhaono1/agent-playbook/blob/main/skills/self-improving-agent/SKILL.md):

- **输入**: `记忆/L4-流水账/sessions/` 近 7 天 jsonl (episodic memory)
- **抽取**: 复发 pattern (applications ≥ 3) + 用户纠正语 → semantic memory
- **落盘**: `记忆/L0-核心/patterns.md` (按 category section 组织)
- **反写提议**: `_assets/evolution-proposals/<date>-<slug>.md`
- **实际 patch**: 用户调 `/cortex:refactor evolution-apply` → AskUserQuestion 接受 → patch SKILL/AGENT

阈值硬编码: `confidence ≥ 0.8 AND applications ≥ 3`。

Safety gate:
- 白名单: `skills/*/SKILL.md`, `skills/*/references/*.md`, `agents/*.md`, `AGENT.md`
- 黑名单: `commands/`, `scripts/`, `_meta/`, `_templates/`
- patch 前要求插件 git working tree clean

详见:

- `scripts/cli/digest.py` (evolution CLI)
- `scripts/cli/lib/evolution.py` (核心逻辑)
- `scripts/refactor/evolution_apply.py` (proposal 消化)
- `skills/cortex-digest/SKILL.md §阶段 8 · Evolution + 清理`
- `skills/cortex-refactor/SKILL.md §evolution-apply`
