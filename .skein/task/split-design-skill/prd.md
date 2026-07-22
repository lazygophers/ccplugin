# split-design-into-color-and-uiux — PRD

## 目标
- [x] skills/design-color/ 独立 skill (主题/配色优化调整设计): SKILL.md + references/(color/ 全 + 4 媒介 style.md + 各媒介精简 INDEX)
- [x] skills/design-uiux/ 独立 skill (UI/UX 布局调整设计): SKILL.md + references/(ui-ux/ 全 + 4 媒介 layout+scenes+components + 各媒介精简 INDEX)
- [x] 删原 skills/design/ (SKILL.md + 全部 references)
- [x] 两 skill 内部链接全 resolve, 无断链

## 边界
- [x] 两 skill references 独立完整副本, 不软链不跨目录引用
- [x] 各媒介 INDEX.md 精简: color skill 的 INDEX 只索引 style 维; uiux skill 的 INDEX 只索引 layout/scenes/components 维
- [x] 两 skill 互相提及对方(配色任务→color skill, 布局任务→uiux skill)走文字提示非链接(独立 skill 不能跨链接)

## 验收标准
- [x] design-color + design-uiux 各有 SKILL.md (frontmatter name+desc 含触发词, desc ≤1024 字)
- [x] 各自 references 无断链
- [x] 原 design/ 已删
- [x] commit 完成

## 索引
- 详细设计: design.md
- 任务/子任务: task.json
