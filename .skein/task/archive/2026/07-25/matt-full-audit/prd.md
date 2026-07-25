# matt skills 全量覆盖审计 — PRD (主入口)

## 目标
- [ ] 审计 matt 全部 22 正式 skills 本体 (已 clone 到 /tmp/mattpocock-skills) 的方法论 vs skein 现状, 产出覆盖差距报告 (每个 skill: 覆盖深度 深/中/弱/空白 + skein 对应位置 + 差距要点)。据报告对弱/空白项补齐 (融入 skein 正文或 references)。目标: matt 全部 skills 方法论在 skein 有对应 (深覆盖或显式超范围标注), 零硬依赖。
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 范围: engineering 17 (ask-matt/grill-with-docs/triage/improve-codebase-architecture/setup/to-spec/to-tickets/implement/wayfinder/prototype/diagnosing-bugs/research/tdd/domain-modeling/codebase-design/code-review/resolving-merge-conflicts) + productivity 5 (grill-me/handoff/teach/writing-great-skills/grilling)。不含 in-progress/personal/misc (实验性非正式)。
- 审计产出报告后, 弱/空白项补齐方式: 深度规则进对应 SKILL.md 正文, 词表/流程进 references; 超范围 (如 teach 非工程) 显式标注不覆盖。零外部 skill 硬依赖。
## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] 产出覆盖差距报告 (findings.md): 22 skills 逐一判定覆盖深度 + skein 对应 + 差距
- [ ] 所有弱/空白项补齐 (融入正文 or references), 或显式标注超范围不覆盖
- [ ] matt-pocock-mapping.md 更新含 resolving-merge-conflicts + grilling 两行 (上次漏)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list matt-full-audit`)
