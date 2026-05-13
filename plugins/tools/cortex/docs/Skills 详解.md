# Skills 详解

cortex 提供 21 个 skill。skill 由 description 池语义匹配自动触发, 也可显式调用 (`/cortex:<相关 command>`)。

## 触发模型

| 触发方式 | skill 数 | 说明 |
|----------|---------|------|
| 自动 (自然语言命中 description Triggers) | ~10 | search / save / ingest / lint / new / recall / memory / consolidate / promote / forget |
| 显式 (`disable-model-invocation: true`) | ~11 | install / schema / session / locale / canvas / dashboard / doctor / refactor / ingest-bulk / html / reflect |

显式 skill 必须用户明确请求, 防止误触发副作用 (写 vault 骨架 / 改语言配置 / 大批量改盘等)。

## 21 个 Skill 速查

**范围标记**: 全局 (用户/系统级) · 当前目录 (PWD) · 知识库 (vault) · 记忆层 (`记忆/L0-L4`)

| Skill | 范围 | 触发 | 用途 | 类型 |
|-------|-----|------|------|------|
| `cortex-install` | 全局+知识库 | "安装 cortex" / "init vault" | 创建 vault 骨架 + 默认模板 + 配置 | 显式 |
| `cortex-schema` | 知识库 | "查 schema" / "frontmatter 字段" | 读 / 校验当前 vault 的 schema | 显式 |
| `cortex-doctor` | 全局+知识库 | "vault 健康吗" / "doctor" | 体检 vault + 依赖 + 配置 | 显式 |
| `cortex-locale` | 全局+知识库 | "切到英文 vault" | 多语言配置 (`_meta/version.json:.lang`) | 显式 |
| `cortex-new` | 知识库 | "新建 concept" / "新文档" | 用模板创建新页面 | 自动 |
| `cortex-save` | 知识库 | "落档 X" / "save this" | 写新笔记 (frontmatter + block-id) | 自动 |
| `cortex-ingest` | 当前目录+知识库 | "ingest <url>" / "深度分析当前目录" | URL / 文件 / git repo / 项目目录 → 知识库 | 自动 |
| `cortex-ingest-bulk` | 知识库 | "批量摄取" | `inbox/urls.txt` 多 URL 批处理 | 显式 |
| `cortex-search` | 知识库 | "搜知识库 X" | hot → index → SC → ripgrep 回退搜索 | 自动 |
| `cortex-recall` | 知识库+记忆层 | "想起 X" / "回忆" | vault + 记忆层语义搜索 | 自动 |
| `cortex-memory` | 记忆层 | "查我的记忆" | 列出 / 查看 / 修改 L0-L4 记忆条目 | 自动 |
| `cortex-promote` | 记忆层 | "升级记忆" | L2 → L1 / L1 → L0 (经用户审批) | 自动 |
| `cortex-forget` | 记忆层 | "忘了 X" | 删除指定记忆条目 | 自动 |
| `cortex-consolidate` | 记忆层 | "整合 ledger" / "consolidate 7 天" | 7 天 ledger → 候选概念页 + 反思 / 连接 | 自动 |
| `cortex-reflect` | 知识库 | "反思" / "出洞察" | 跨页面生成反思 / 连接 / 疑问页 | 显式 |
| `cortex-session` | 知识库 | "导入 session" | jsonl transcript → 知识库 sessions/ | 显式 |
| `cortex-lint` | 知识库 | "vault 体检" / "lint" | 跑 17 条规则 + autofix 循环修复 | 自动 |
| `cortex-refactor` | 知识库 | "改名" / "合并 / 拆分" | 改名 / 合并 / 拆分页面 + 同步 wikilink | 显式 |
| `cortex-canvas` | 知识库 | "渲染 canvas" | 生成 / 刷新 Obsidian canvas 图 | 显式 |
| `cortex-dashboard` | 知识库 | "刷新仪表盘" | 重渲 index.md / hot.md / canvas | 显式 |
| `cortex-html` | 知识库 | "渲染 HTML 卡片" | 把 frontmatter / 数据渲染为 inline HTML | 显式 |

## 行为约束 (AUTO_MODE persistent, 所有 skill 一致)

shell wrapper / slash command 触发时:

- **禁询问**: AskUserQuestion 工具不可用
- **禁中止**: 报状态后停 = 违规, 必须循环修复直至稳定 或 工具客观失败 (磁盘只读 / 权限拒绝 / git lock)
- **禁推卸**: "需人工" / "AI 不会" / "建议后续处理" 等推卸辞令禁止输出
- **自决执行**: 遇歧义按推荐默认值执行; 工具不熟悉则尝试其他组合 (Bash / Edit / Write / MCP / WebSearch / Read 现有样本)

IDE 内交互模式不受此约束, 可走 `AskUserQuestion` 4 选项流程。

## Skill 详细文档

每个 skill 的完整描述 / 触发短语 / 失败处理见 `skills/<name>/SKILL.md`。
