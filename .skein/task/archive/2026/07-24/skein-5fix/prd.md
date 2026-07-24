# skein 5点修正 — PRD (主入口)

## 目标
- [ ] findings.md 增量落盘且仅调研时产出
- [ ] check 失败按错误性质回 plan 补 design/prd/subtask
- [ ] check 场景自适应扩至 6 类
- [ ] spec 类 agent 标纯异步不阻塞
- [ ] agent 绑定对应 skill
## 边界
- 只改 skein 插件自身 7 md + skein.py + mmd
- 不改 spec 核心引擎逻辑
- 不引入新 skill 文件
## 验收标准
- [ ] create 不再预建 findings.md
- [ ] researcher 边研边增量写 findings.md
- [ ] skein-check 场景 6 类齐备
- [ ] skein-check step3 覆盖 design/prd/subtask 补充
- [ ] specer/dedup 带 skein_dispatch:async 自定义字段
- [ ] executor 绑 skein-exec skill
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-5fix`)
