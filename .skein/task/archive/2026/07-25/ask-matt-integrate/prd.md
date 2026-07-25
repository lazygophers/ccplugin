# ask-matt 场景路由融入 skein — PRD (主入口)

## 目标
- [ ] 将 /ask-matt (Matt Pocock 场景路由器) 的场景路由理念融入 skein。两处改动: (1) skein-flow SKILL.md 作用域边界表扩展为场景路由表 (新idea/雾区大需求/bug堆积/难bug/代码健康/设计问题 → skein内置走法); (2) 新建 skein-flow/references/matt-pocock-mapping.md 完整 ask-matt->skein skill 映射, handoff 行标注已由 task.json+工件+sediment 替代不单列。零外部 skill 硬依赖, 外部 skills 仅在 mapping 文件标注可选引用未装跳过。
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 仅改 skein-flow SKILL.md 作用域边界表 + 新建 skein-flow/references/matt-pocock-mapping.md; 不新建 skill; 不动 plan/exec/check/finish 正文 (handoff 不写); 零外部 skill 硬依赖
- 用户交互归 plan 前置 (场景路由判定在 plan 及之前); 无 exec/check/finish 新交互
## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] skein-flow SKILL.md 作用域边界表含场景路由行 (新idea/雾区需求/bug/代码健康等至少 5 类信号)
- [ ] skein-flow/references/matt-pocock-mapping.md 存在, 含 ask-matt 全部 skill 的映射 (grill/grill-with-docs/grill-me/to-spec/to-tickets/implement/tdd/code-review/triage/diagnosing-bugs/wayfinder/improve-codebase-architecture/domain-modeling/codebase-design/handoff/compact/prototype/research/teach/writing-great-skills/setup)
- [ ] mapping 文件 handoff 行标注: 已由 task.json+工件+sediment 替代不单列
- [ ] skein-flow SKILL.md 加指针指向 matt-pocock-mapping.md
- [ ] grep 外部 skill 名仅在 mapping 文件出现, skein-flow 正文零外部 skill 名 (零硬依赖)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list ask-matt-integrate`)
