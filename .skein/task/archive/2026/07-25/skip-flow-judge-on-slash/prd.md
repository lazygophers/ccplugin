# slash 命令跳过 flow 判定注入 — PRD (主入口)

## 目标
- [x] hooks.py cmd_user_prompt: prompt strip 后以 /skein- 或 /skein:skein- 开头时, 跳过 _CTX flow 判定注入 (return 0 不输出 additionalContext), 因用户已显式调 skein slash command 无需路由启发
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 仅 cmd_user_prompt 一处; 前缀匹配在 strip 后判; 其他 hook 不动; 未初始化提示仍正常 (slash 调 skein 命令也需 init)
## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] prompt='/skein-plan xxx' → 无 SKEIN 判定注入
- [ ] prompt='改 hooks.py' → 仍注入 SKEIN 判定 (非 slash 开头)
- [x] prompt=/skein:skein-flow xxx → 无 SKEIN 判定注入
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skip-flow-judge-on-slash`)
