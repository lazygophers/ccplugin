# 优化 skill-dev 全部 skill 对齐 mattpocock/skills — PRD (主入口)

## 目标
深度对齐 Matt Pocock `skills` 仓的权威 skill 编写范式, 重构 `skills/skill-dev/` 下三 skill:
- [ ] 三 skill **相互无依赖** (现状已无跨文件夹链接, 依赖是 `/skill` prose — 符合 Matt 铁律, 保持)
- [ ] **optimize-any 同步进 skill-dev/plugin-dev 流程 B 后移除** (它=通用优化循环纪律, 冗余)
- [ ] 每个 skill 有**报告模板** (inline `<report-template>` 围栏, 创建报告 + 优化报告)
- [ ] 每个 skill **默认正向表述, 仅必要场景保留反例** (对齐 Matt negation 末选), 且要求被创建/优化的目标也禁反例
- [ ] **rubric 加方向轴 + 理想值** (混合: 量化评分 + 完成准则底线), 确保多次优化往期望方向收敛
- [ ] 全量对齐 mattpocock 调研结论 (patterns + philosophy)
- [ ] 完成输出各 skill **评分机制汇总** 给用户定夺后续

## 边界
范围内:
- [ ] 改 `skills/skill-dev/skill-dev/` (SKILL.md + references/dimensions.md + 视情况其他 ref)
- [ ] 改 `skills/skill-dev/plugin-dev/` (SKILL.md + references/optimize-rubric.md)
- [ ] 删 `skills/skill-dev/optimize-any/` (整目录)
- [ ] 改 `skills/skill-dev/README.md`
- [ ] 产出评分机制汇总

范围外 (非目标):
- [ ] 不加 `agents/openai.yaml` (本仓只跑 Claude Code)
- [ ] 不动 `references/research/01-06.md` + `optimizer-sources.md` (调研素材)
- [ ] 不改 skill 触发方式 (disable-model-invocation 保持)

已知约束:
- [ ] 项目 CLAUDE.md: 改 SKILL.md 后必须过 `claude -p` 质量门
- [ ] 变更自动 git add + commit (禁 push)

## 验收标准
- [x] 三 skill 无跨文件夹文件链接 (grep 验证)
- [x] optimize-any 目录已删, 其内容已拆进 skill-dev/plugin-dev 流程 B
- [x] 三 skill 各有 inline `<report-template>` 围栏 (创建 + 优化两份)
- [x] 三 skill 主体正向表述, 反例仅留必要硬护栏并配正例
- [x] 三 skill rubric 有方向轴 + 理想值列
- [x] 三 skill 要求目标 skill 也禁反例 (传递要求)
- [x] claude -p 质量门三 SKILL.md 全过
- [x] 评分机制汇总文档交付

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) + research/mattpocock-skills-*.md
- [ ] 任务/子任务/调度: task.json (`skein subtask list skill-dev-align-mattpocock`)
