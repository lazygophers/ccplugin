# DAG 节点 hover popover + click Modal 浮窗 — PRD (主入口)

## 目标
- [ ] hover 浮窗: 鼠标悬停 DAG 节点 → 弹富文本 popover (替代原生 <title>), 显: 节点名+状态 / 上下游依赖 / 描述+进度条。
- [ ] click 浮窗: 点击节点 → 弹 <dialog> Modal 全量详情 (同 popover 字段但更大版 + 可滚动)。
- [ ] 成功: DAG tab 节点 hover 见 popover, click 见 Modal, 4 态各有合理字段值, prefers-reduced-motion 不影响。

## 边界
范围内:
- [ ] `docs/examples/index.html` 单文件改: DAG panel 节点结构 + CSS (popover/Modal) + 极小 JS (dialog showModal/close)。
- [ ] popover 纯 CSS (节点 hover → 浮窗显), Modal 用原生 <dialog>.showModal() (复用现有 Modal 范式 L256)。
- [ ] 节点数据 (上下游/耗时/描述) 内联 data-* 属性或写死示例值 (无后端)。

范围外 (非目标):
- [ ] 不改其他 5 tab。
- [ ] 不引第三方 popover/modal 库 (复用原生 <dialog> + CSS)。
- [ ] 不改节点拓扑/4 布局结构。
- [ ] 不接真后端数据 (示例值即可)。

## 验收标准
- [x] hover: 节点悬停 → 自定义 popover 显 (名称+状态徽标 / 上下游节点列表 / 描述文本 + 进度条), 替代原生 title 灰条。
- [x] click: 节点点击 → <dialog> Modal 弹全量详情, ESC/点遮罩关闭。
- [x] 4 态节点各有合理字段 (done 显已完成耗时 / active 显进度%+实时 / failed 显失败原因 / 默认显待执行)。
- [x] popover 不被 SVG viewBox 裁切 (用 HTML overlay 定位而非 SVG 内 text)。
- [x] 浏览器打开无 JS 报错, 6 tab 切换流畅。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list dag-popover`)
