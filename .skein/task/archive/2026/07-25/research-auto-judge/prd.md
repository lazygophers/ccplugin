# research 判定门自动化 — PRD (主入口)

## 目标
- [ ] skein-plan planning 阶段自动判断是否派 skein-researcher, 按信号分档自动判 (明确需/明确不需/保守灰区/激进灰区/兜底), 非用户说要才派
## 边界
- 范围内: skein-plan SKILL.md 加 research 判定门 section + 调 L13 措辞
- 范围外: hook 机械化信号; skein-researcher agent 本身; 其他 skill
- 约束: 单文件改, 零功能变更 (仅 skill 文案)
## 验收标准
- [x] skein-plan SKILL.md 含 research 判定门 section (五档表)
- [x] L13 措辞从「可派」改为指向判定门
- [x] claude -p 质检过 (AI 能正确理解判定门触发)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list research-auto-judge`)
