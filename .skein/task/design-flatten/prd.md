# flatten-design-to-one-skill — PRD

## 目标
- [x] skills/design/ 成为一个独立 skill: 根 SKILL.md 唯一
- [x] medium(html/app/cli/tui) 降为内部模式, 各 medium 内容进 references/
- [x] 多文件组织保留(用户此前要求)
- [x] 删 html-design/app-design/cli-design/tui-design 子 skill 目录与 README

## 边界
- [x] 只一个 SKILL.md (在 skills/design/ 根)
- [x] references/ 下文件不是 skill, 是参考
- [x] frontmatter ≤1024, 禁角色自述, 无反模式段

## 验收标准
- [x] skills/design/SKILL.md 存在且为唯一 SKILL.md
- [x] 无 html-design/app-design/cli-design/tui-design 目录
- [x] references/ 含各 medium 文件
- [x] git commit 完成

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json
