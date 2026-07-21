# hook 判定权全交 AI: 删脚本预筹+文案加强 — PRD (主入口)

## 目标
- [ ] UserPromptSubmit hook 移除脚本预筹判断行为(_classify_prompt 3档), 只注入'判 flow vs 豁免'的判断标准提示词, 判定权全交 AI
- [ ] AI 判走 flow 后不再用'但先探索''TaskCreate冒充skein create'等借口自降级 inline
## 边界
- 范围: 仅 UserPromptSubmit hook (skein.py user_prompt + _classify_prompt)
- 范围外: 其他 hook (SessionStart/SubagentStart/PreToolUse/Stop 等) 不动
- 范围外: 不加 PreToolUse 落码守卫 (用户未要求方案1)
## 验收标准
- [ ] skein.py 中 _classify_prompt 方法及其调用全部删除 (grep -c == 0)
- [ ] user_prompt 只注入判断标准提示词, 无脚本预筹档位输出
- [ ] 文案含判定行禁修饰词(但/先/只是)的硬规
- [ ] 文案明确 TaskCreate(harness内置)≠skein create, 禁冒充
- [ ] claude -p 质量门: AI 能正确理解'判走flow后禁自降级'
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list hook-prompt-judge-ai-only`)
