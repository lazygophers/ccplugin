# 修 skein plugin.json 尾逗号 — PRD (主入口)

## 目标
- [ ] 删 skein/.claude-plugin/plugin.json UserPromptSubmit hook command 行尾逗号, 修 JSON parse error
## 边界
- 范围内: 仅删该尾逗号; 范围外: 不动其他 plugin.json、不改 hook 逻辑
## 验收标准
- [ ] python3 -c json.load 解析 8 个 plugin.json 全通过
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list fix-skein-plugin-json`)
