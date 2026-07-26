# DAG tab 动效与设计增强 — PRD (主入口)

## 目标
- [ ] hover 动效: DAG 节点 hover 放大 + 对应边高亮 + tooltip (节点说明悬浮显)。
- [ ] 入场动效: 切到 DAG tab 时节点级联淡入 (按深度错峰 stagger)。
- [ ] 蚂蚁线流动边: active 边 stroke-dashoffset 动画, 模拟数据流。
- [ ] 图例徽标: DAG panel 顶部图例条 (4 态色 + 边类型: 实/虚/active)。
- [ ] 状态图标: 节点旁附状态图标 (✓ done / ⏳ active / ✗ failed / ○ pending)。
- [ ] 成功: 打开 DAG tab, 五项可见可交互, prefers-reduced-motion 退化为静态。

## 边界
范围内:
- [ ] `docs/examples/index.html` 单文件改: DAG panel `<section data-tab="dag">` + `.dag-svg` CSS 块。
- [ ] 复用海滩蓝金色板 + .dag-svg 类名约定, 不破 4 布局结构。
- [ ] 所有动效必须 `@media(prefers-reduced-motion:reduce)` 退化。

范围外 (非目标):
- [ ] 不改其他 5 tab (色卡/组件/图表/动效/Timeline)。
- [ ] 不引第三方动画/图表库 (保持 tailwind+font-awesome CDN)。
- [ ] 不改节点拓扑/数量 (4 布局变体 22 节点保持)。
- [ ] 不加 JS 动画引擎 (纯 CSS @keyframes + transition)。

## 验收标准
- [x] hover: 节点悬停 scale 放大 + 对应边 stroke 加粗高亮 + tooltip 显节点说明。
- [x] 入场: 切到 DAG tab → 4 SVG 节点按深度级联淡入 (≤1s, SVG 内 stagger)。
- [x] 蚂蚁线: active 边持续单向流动 (stroke-dashoffset 动画)。
- [x] 图例: DAG panel 顶部图例条显 4 态色 + 3 边类型。
- [x] 状态图标: 4 态节点各显 ✓/⏳/✗/○。
- [x] prefers-reduced-motion:reduce 下所有动画停止, 静态可读。
- [x] 浏览器打开无 JS 报错, 6 tab 切换流畅。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list dag-motion-design`)
