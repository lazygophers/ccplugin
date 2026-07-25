# design skills 深度优化（流程 B 9维评分+爬山） — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 对 design-uiux 和 design-color 两 skill 跑 9 维独立评分诊断，找最薄弱维度
- [ ] validation-gated 单变量爬山优化：每轮只改 1 维度，独立 judge before/after 对比，Δ>0 才 ratchet 落地
- [ ] 解决结构性缺口（typography 归属边界 / 姊妹 skill 交叉模糊 / 触发词覆盖）
- [ ] 改后过 claude -p 质量门确认 AI 可正确识别

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内：SKILL.md 优化 + 触发词/路由修复 + INDEX 挂载修正；references 数据文件不重写
- [ ] 范围外：不重构媒介目录结构（html/cli/tui/app 三维保留）；不删现有数据
- [ ] 约束：破坏性变更（触发词/description）必须用户确认；膨胀护栏改后≤原×1.5；auto-commit 每轮

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] 9 维评分诊断完成（2 judge 共识，行号引用）
- [ ] 最薄弱维度经爬山优化 Δ>0（ratchet 落地，非 dry_run 占满分）
- [ ] typography 归属边界明确（color vs uiux 无交叉模糊）
- [ ] 改后 SKILL.md 过 claude -p 质量门（返回非空且识别正确）
- [ ] 无 runtime 红灯；膨胀 ≤ 原×1.5

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list design-skills-optimize`)
