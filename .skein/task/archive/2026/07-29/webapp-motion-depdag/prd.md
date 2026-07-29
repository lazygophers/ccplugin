# webapp 呼吸动效 + 依赖关系图落位 — PRD (主入口)

## 目标
- [ ] 看板/详情页「执行中」态有明确可感的呼吸动效 (用户裁定: 光晕扩散 + 微缩放), 现有 tlPulse/dagPulse 视觉近乎不可见
- [ ] 有前置或后置依赖的 task, 在 task 详情页也能看到依赖关系图 (现只有文字链接列表)
- [ ] board detailPanel 的依赖关系图从最底部上提, 减少滚动才能看到的问题
## 边界
- 范围内: plugins/tools/skein/assets/webapp/src/ 下 design.css / new/pages/task.js / new/pages/board.js / 新建 new/lib/depdag.js
- 范围外: 后端 skein.py / serve 端点 / 任何 API 契约变更; task 详情端点保持自足 (禁为画图去拉 /data 全量看板)
- 约束: SVG 元素不支持 box-shadow — design.css:1315 的 .dag-svg .node.active 必须单独用 SVG 可行手段 (drop-shadow/opacity), 禁把 box-shadow 方案套上去
- 约束: prefers-reduced-motion (design.css:1874-1885) 必须继续把全部循环动效关掉, 新增选择器要补进该列表
- 约束: 禁在 path 上加参数, 所有参数走 query 形式
## 验收标准
- [ ] tlPulse 改为 0%/100% box-shadow 0 0 0 0 <色 55% alpha> + scale(1); 50% box-shadow 0 0 0 7px 透明 + scale(1.15), 周期 1.8s
- [ ] 新增 dagBreathe keyframes (box-shadow 光晕扩散 + 轻微 scale), .dag-node.st-active / .dag-pop-badge.active / .antd-tag-active 三处 HTML 选择器改用它
- [ ] dagPulse 保留但仅供 SVG (.dag-svg .node.active), 改为 SVG 可见的呼吸 (drop-shadow 强弱起伏), 不再是纯 opacity 闪烁
- [ ] prefers-reduced-motion 媒体查询覆盖全部新增/改名后的动效选择器, 无遗漏
- [ ] 新建 new/lib/depdag.js, 导出 buildDepDAG + depDAGView (含其依赖的 drawEdges 一族), board.js 改为 import 该模块, 无重复实现
- [ ] task.js 详情页左栏「被依赖」卡下方新增「依赖关系图」卡片: 仅当 depTasks.length 或 dependents.length 非零时渲染, 数据用 [task, ...depTasks, ...dependents] 喂 buildDepDAG, 不新增网络请求
- [ ] board.js detailPanel 依赖关系图块位置上提到「子任务 DAG」之前
- [ ] 静态核对: node --check 各改动 js 文件语法通过; grep 核对 dagPulse 仅剩 SVG 选择器引用; 无残留旧 keyframes 死代码 (用户裁定验收方式=静态核对+自行目视)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list webapp-motion-depdag`)
