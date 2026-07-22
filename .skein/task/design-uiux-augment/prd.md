# design skills 增量补齐 ui-ux-pro-max 数据 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 学习 nextlevelbuilder/ui-ux-pro-max-skill 的设计智能数据，增量补齐 skills/design 下 design-color 与 design-uiux 两 skill 缺失的参考维度
- [ ] 补齐后 design skills 覆盖：100 行业推理规则 / 10 类 UX 规则全量 / 67 UI 风格 / 57 字体配对 / 25 图表类型 / app native polish checklist
- [ ] 不破坏现有结构（SKILL.md 路由 / 三方向门 / 姊妹 skill 互引 / 各媒介 INDEX 全保留）

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内：新增 references 数据文件 + 挂进对应 INDEX.md + SKILL.md 方法论表加新条目
- [ ] 范围外：不重写现有 SKILL.md 路由逻辑；不改 frontmatter name/description；不迁移现有 scenarios.md/themes-catalog.md/palettes-catalog.md
- [ ] 约束：遵循 skein-pwd-only（只按仓库根操作）；auto-commit 每个 batch

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] design-uiux/references/ui-ux/industry-rules.md 存在，含全部 100 行业（按 11 大类分组）
- [ ] design-uiux/references/ui-ux/rules.md 存在，含 10 类 UX 规则（accessibility/touch/performance/style/layout/typography-color/animation/forms/navigation/charts）
- [ ] design-color/references/color/styles-catalog.md 存在，含 67 UI 风格（49 通用 + 8 落地页 + 10 BI）
- [ ] design-color/references/color/typography.md 存在，含 57 字体配对 + Google Fonts 指引
- [ ] design-uiux/references/ui-ux/charts.md 存在，含 25 图表类型选型
- [ ] design-uiux/references/{html,app,cli,tui}/ 的 INDEX 或新 polish.md 挂载 pro-rules checklist（app native polish）
- [ ] 各新文件被对应 INDEX.md 或 SKILL.md 方法论表引用（无孤儿文件）
- [ ] 所有内部链接无断链

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list design-uiux-augment`)
