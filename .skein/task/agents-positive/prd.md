# agent 文档正向化 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 9 个 agent 文件里的约束改用**正向可执行**表述 —— 读者拿到的是「该做什么」, 而不是「不该做什么」后自己反推。
- [ ] 约束强度**一条不丢**: 每条否定式转写后, 原有的边界、理由 (why) 与失败后果都保留。
- [ ] 跨文件重复的同类条目收敛为一处措辞统一, 不再 9 份各说各话。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 范围内: `plugins/tools/skein/agents/*.md` 全部 9 个文件的正文措辞。
- 范围外: agent 的能力边界与工作流步骤本身 (只改怎么说, 不改做什么); frontmatter 字段; skills/ 与 docs/ 下的文档。
- 约束: `🛑` / `❌` 等标记符号保留 —— 它们标的是「这是硬约束」, 与措辞正负无关。
- 约束: 转写后语义等价, 禁借正向化之名放宽约束 (如「禁全仓回滚」不可弱化成「谨慎使用回滚」)。
- 约束: 少数否定式无正向等价 (如「本 agent 无 Write/Edit 权限」是能力事实陈述), 保留原样并在验收时列出豁免清单。

## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a subagent, I want 每条约束直接告诉我该执行什么动作, so that 不必从禁令反推出唯一合法路径。
2. As a subagent, I want 转写后仍看得到「为什么」, so that 遇到文档没覆盖的情形能按同一原则判断。
3. As a subagent, I want 同一条公共约束在 9 个文件里措辞一致, so that 不会因表述差异误判成不同规则。
4. As a 维护者, I want 无正向等价的条目有明确豁免清单, so that 后续 review 不会反复纠结这几条。
5. As a 维护者, I want 转写不改变工作流步骤, so that diff 只落在措辞上, 易于核对。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] 9 个文件中的否定式表述 (禁/不得/不要/勿/不准/不该) 全部转为正向, 或列入豁免清单并说明理由。
- [x] 逐条比对转写前后语义等价: 每条给出「原文 → 新文」对照, 边界与 why 无丢失。
- [x] 跨文件重复的同类约束措辞统一 (公共铁律、工具失败标记、缺信息回传 三类至少各收敛为一种措辞)。
- [x] 工作流步骤、章节结构、frontmatter 未被改动 (diff 只落在正文措辞)。
- [ ] 9 个文件均通过 AI 理解度检查, 主流程描述与改写前一致。

## 验证方式
每条验收标准的验证手段与通过标准 (plan 阶段必填):
- 残留扫描: `grep -c "禁\|不得\|不要\|勿\|不准\|不该" plugins/tools/skein/agents/*.md` —— 通过标准: 命中项全部出现在豁免清单里。
- 语义等价核对: 人工逐条读「原文 → 新文」对照表 —— 通过标准: 无一条约束被放宽或丢失 why。
- 结构未动: `git diff --stat` + 逐文件 diff —— 通过标准: 无章节增删、无 frontmatter 改动。
- AI 理解度 (项目 CLAUDE.md 强制): `cat <文件> | claude -p --bare "<该文件的触发场景与主流程是什么>" --output-format stream-json 2>/dev/null | jq -r 'select(.type=="result" and .subtype=="success") | .result'` —— 通过标准: 返回非空且切题, 同一 prompt 连跑 3 次主流程描述一致。端点报 ConnectionRefused 属抖动, 重跑而非当结论。
- 回归: `uv run pytest plugins/tools/skein/scripts/tests/test_docs_commands.py` —— 通过标准: 全绿。

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- 本任务是文档改写, **不新增自动化测试** —— 无代码行为可测, 为措辞写断言只会锁死措辞、阻碍后续优化。
- 主检验手段是项目 CLAUDE.md 规定的 AI 理解度检查 (stdin 管道 + `--bare` + `2>/dev/null`), 它测的正是「AI 能否正确理解」这一真实外部行为。
- 既有 `test_docs_commands.py` 会校验文档里出现的命令可用, 作为回归兜底, 沿用不改。

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein subtask list agents-positive`)
