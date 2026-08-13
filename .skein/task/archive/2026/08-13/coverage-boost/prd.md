# 测试覆盖率提升到95% — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
- [ ] 确保 plugins/tools/skein/scripts/ 测试覆盖率 >95% 且通过率 100%
## 边界
- 不修改 skeinlib/ 源码逻辑只加测试
## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a <actor>, I want <feature>, so that <benefit>

## 验收标准
- [ ] coverage report 总覆盖率 ≥95%
## 验证方式
- coverage report --sort=-miss TOTAL miss ≤312
## Testing Decisions
- [ ] hooks 模块模拟 stdin JSON + monkeypatch 环境
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein subtask list coverage-boost`)
