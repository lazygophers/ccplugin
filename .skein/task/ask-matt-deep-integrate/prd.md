# ask-matt 方法论深度融入 skein — PRD (主入口)

## 目标
- [ ] 吸收 ask-matt 4 条独立方法论深度融入 skein 正文/references (上次只做了场景路由表+映射文件, 本次是方法论本体进正文): (1) smart zone+context hygiene 进 skein-plan; (2) tracer-bullet 端到端瘦实现优先进 skein-plan subtask 拆分铁律; (3) tight feedback loop 先复现再修进 skein-exec 自愈; (4) deep-module 词表(module/interface/depth/seam/adapter/leverage/locality)+ADR 进 skein-plan/references/design-vocabulary.md。第5条协议先行后并行 skein-plan L99 已覆盖, 仅强化与 tracer-bullet 衔接。
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 改 skein-plan SKILL.md (smart zone section + subtask 拆分铁律加 tracer-bullet); 改 skein-exec SKILL.md (自愈加 tight feedback loop); 新建 skein-plan/references/design-vocabulary.md (deep-module 词表+ADR); 不新建 skill; 零外部 skill 硬依赖
- 交互归 plan 前置; exec/check/finish 无新交互 (tight feedback loop 是 subagent 内纪律非用户交互)
## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] skein-plan SKILL.md 含 smart zone / context hygiene 概念 (grill->prd->subtask 同 context 不中途 compact, 接近 120k token 先收敛/派 researcher 而非 degraded 推进)
- [ ] skein-plan SKILL.md subtask 拆分铁律含 tracer-bullet 原则 (契约 subtask 本身是端到端穿通最瘦实现, 验证全链路后再 flesh)
- [ ] skein-exec SKILL.md 自愈段含 tight feedback loop 硬门 (subtask 失败先建一条就红的复现命令/测试再修, 禁盲改)
- [ ] skein-plan/references/design-vocabulary.md 存在, 含 deep-module 词表 (module/interface/depth/seam/adapter/leverage/locality) + ADR 机制 (难逆决策记录)
- [ ] skein-plan SKILL.md design.md 段加指针指向 design-vocabulary.md
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list ask-matt-deep-integrate`)
