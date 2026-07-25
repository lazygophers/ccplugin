# add-design-skills — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [x] 在 ccplugin skills/ 新增 design 分类，提供 HTML-first 设计能力（对标 huashu-design / baoyu-* 但聚焦自包含）
- [x] 覆盖 UI/UX 界面 / 数据可视化 / 图像设计 / 演示排版 四模式，所有产出以 HTML 落地，其余格式从 HTML 打包导出
- [x] 单 skill 内部路由区分组件级 / UX 级 / 可视化 / 图像 / 演示

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [x] 范围内: skills/design/README.md + skills/design/html-design/SKILL.md
- [x] 范围外: 不移植 huashu-design 的 28 个 references 巨物；不接入真实导出脚本依赖（仅写管线约定）
- [x] 约束: SKILL frontmatter description ≤ 1024 字；禁「你是…」角色自述开头；脚本/机械优先
- [x] 不适用: 需后端的动态系统、生产级 Web App、SEO 站点

## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] skills/design/README.md 存在，含分类说明 + 路由表，风格对齐 code-quality/README
- [x] skills/design/html-design/SKILL.md frontmatter 含 name + description（触发词齐全）
- [x] SKILL 含三方向初稿硬门 + 四模式路由表 + 各模式细则 + 导出管线 + 反模式
- [x] claude -p 质量门返回非空有意义
- [x] git commit 完成

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list design-skills`)
