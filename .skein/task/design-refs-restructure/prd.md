# restructure-refs-by-medium-dim — PRD

## 目标
- [x] references/ 改为 references/{html,app,cli,tui}/ 四 medium 目录
- [x] 每 medium 内按 4 维拆: layout(布局/设计) / scenes(场景) / components(组件) / style(设计风格)
- [x] 每 medium 一个 INDEX.md 二级索引 + 选择指导
- [x] HTML 保留 genre 文件(data-viz/image/slides/export)作 medium 特有补充
- [x] 顶层 SKILL.md 改引用各 medium INDEX.md

## 边界
- [x] 唯一 SKILL.md 仍在 skills/design/ 根
- [x] INDEX.md 不带 skill frontmatter(非 skill, 是二级索引)
- [x] 无反模式段, frontmatter 达标

## 验收标准
- [x] 4 medium 目录各含 INDEX + layout + scenes + components + style
- [x] html/ 额外含 data-viz/image/slides/export
- [x] 顶层 SKILL.md 引用各 INDEX.md
- [x] git commit 完成

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
