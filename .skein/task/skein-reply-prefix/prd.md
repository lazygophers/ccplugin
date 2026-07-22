# 回复前缀强制注入 — PRD (主入口)

## 目标
- [ ] 每条回复强制前缀: 默认 [skein]; 处理某 task 时 [skein|<taskId>|<phase>] (phase: plan/exec/check/research)
- [ ] 经 SessionStart(skein.py session_context) + UserPromptSubmit(hooks.py cmd_user_prompt) 注入指令 + 动态 active task 提示
## 边界
- 范围内: 两注入点各追加前缀规则文本 + active task/phase 清单 (从 .skein/task.json 索引读, status→phase 映射)
- 范围外: 无法真正改写 AI 输出 (仅注入指令软约束); 不改 _CTX 判定逻辑
## 验收标准
- [ ] UserPromptSubmit 注入含前缀规则 + 当前 active task(phase)
- [ ] SessionStart 注入含同规则
- [ ] status→phase: 待处理=plan 进行中=exec 检查中=check
- [ ] pytest 全绿
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-reply-prefix`)
