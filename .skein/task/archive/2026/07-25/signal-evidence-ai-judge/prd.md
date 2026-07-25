# _judge_signal 改证据展示 — PRD (主入口)

## 目标
现 `_judge_signal` 替 AI 做最终判定 (return flow/inline/grey → 注死对应常量), 不符预期。改为: 信号检测作**证据展示 + 建议**, 最终走 flow/inline 由 AI 判。

## 边界
- [ ] 范围内: hooks.py `_judge_signal` + `_CTX_FLOW/_CTX_INLINE/_CTX_GREY` + cmd_user_prompt
- [ ] 范围外: cmd_task_created / cmd_guard (机械硬门不动, 与本改动正交)
- [ ] 约束: **token 精简** — 注入文案每 prompt 常驻, 忌冗长

## 验收标准
- [x] `_judge_signal` 返回命中信号证据清单 (非仅档位), 或新辅助 `_detect_signals`
- [x] 三常量各含: 判断条件展示 (flow/inline/判不清) + 命中信号证据 + 建议语调 (flow/grey 档非强制)
- [x] token 控制: 三常量各 < 200 字, 不重复条件段
- [x] python ast 过 + --self-check 更新 (信号证据断言)
- [x] negation 仍清 (无 MUST/禁/违规/黑名单)

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list signal-evidence-ai-judge`)
