# split-design-by-medium — PRD

## 目标
- [x] skills/design/ 按 medium 拆为独立 skill: html(已有) / app / cli / tui
- [x] 每个 medium skill 自包含(SKILL.md + 按需 references)
- [x] README 改为 medium 路由索引

## 边界
- [x] html-design 保留不动
- [x] 每个 skill frontmatter description ≤1024 字, 禁角色自述, 含触发词
- [x] 不出现反例段

## 验收标准
- [x] app-design/ cli-design/ tui-design/ 三个 SKILL.md 存在
- [x] README 含 medium 路由表(html/app/cli/tui)
- [x] 各 frontmatter 达标
- [x] git commit 完成

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
