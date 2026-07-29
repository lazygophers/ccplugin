# index.html 加 DAG 样例 tab — PRD (主入口)

## 目标
- [ ] 加 DAG tab: 通用 DAG 组件变体 (竖向树/水平 DAG/菱形/并行分支), 纯 SVG+CSS, 复用海滩蓝金色板
- [ ] 节点支持状态色 (默认/激活/完成/失败), 边支持箭头/虚线
- [ ] 成功: DAG tab 可切换, 多布局 DAG 渲染清晰
## 边界
- [ ] docs/examples/index.html 单文件: 加 DAG tab 按钮 + panel + SVG/CSS
- [ ] 纯 SVG+CSS, 不引图库 (mermaid/d3 等)
- [ ] 不改其他 tab / tailwind.config
## 验收标准
- [x] DAG tab 存在可切换 (第 6 个 tab 按钮)
- [x] 含 ≥4 种 DAG 布局变体 (竖向树/水平 DAG/菱形/并行分支)
- [x] 节点状态色齐全 (默认/激活/完成/失败)
- [x] 边有箭头, 部分虚线表可选/弱依赖
- [x] 纯 SVG+CSS 无图库依赖
- [x] 复用海滩蓝金色板, 明暗双模可读
- [x] 浏览器打开无 JS 报错, 6 tab 切换全通
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list examples-dag`)
