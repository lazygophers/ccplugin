# skein agents 全量母版化重设计 — PRD (主入口)

## 目标
把 `plugins/tools/skein/agents/` 下 7 个非母版 agent (specer/executor/setup/recaller/dedup/researcher/finisher) 全量对齐 `skein-checker.md` 的四要素范式, 让 8 个 agent body 结构统一、可预测、失败可上报。skein-checker.md 是母版, 不动。

## 边界
范围内:
- [ ] 7 个 agent body 重写为四要素: ①工作流 (编号 checklist + ``` 命令块) ②Checkpoints (🛑 视觉标记) ③返回数据格式 (JSON, 仅各自专有键) ④失败模式 (if-then 三段式表: 触发/一线处理/兜底)。
- [ ] 删每个 agent 开头的角色说明段 ("你是 SKEIN 的...")。
- [ ] 每个 agent body 内联 `[工具失败:原因]` 标注约定 (自包含)。
- [ ] 公共铁律保留为引用 `core/agent/skein-skill-agent-slim-01` (不内联展开)。
- [ ] 补 frontmatter 缺口: skein-executor 补 model; skein-dedup 补/核 skills; 核对全部 frontmatter 齐整。
- [ ] 每个改后 .md 过 `claude -p` 质量门。

范围外 (非目标):
- [ ] 不改 skein-checker.md (母版)。
- [ ] 不改 agent 的职责语义/工具集/触发逻辑 (仅重构 body 表达 + 补缺字段)。
- [ ] 不改 skills/commands/scripts。

已知约束:
- [ ] 失败上报只陈述原因, 禁分类标签 (retry N/3、环境性、端点抖动)。见记忆 failure-report-no-classify。
- [ ] 质量门端点抖动 400 → 重试循环 8 次; 仍败人工验 + 标「待端点恢复补跑」。
- [ ] JSON 返回仅用各 agent 自己的专有键, 不强加公共键。

## 验收标准
- [ ] 7 个 agent body 均含四要素 (工作流/Checkpoints 🛑/返回 JSON/失败 if-then 表), 结构对齐母版。
- [ ] 7 个 agent 均无「你是 SKEIN 的...」角色段。
- [ ] 每个 agent body 内联 `[工具失败:原因]` 约定。
- [ ] 公共铁律仍以 `core/agent/skein-skill-agent-slim-01` 引用形式保留。
- [ ] frontmatter 缺口补齐 (executor model; dedup skills), 全部 name/description/tools 齐。
- [ ] 每个改后 .md 过 `claude -p` 质量门返回非空且识别正确 (或标「待端点恢复补跑」)。
- [ ] 变更自动 git add + commit (禁 push)。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list agent-redesign`)
