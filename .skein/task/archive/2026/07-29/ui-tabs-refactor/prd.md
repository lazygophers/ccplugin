# UI 样例模板改 4 tab 组织 — PRD (主入口)

## 目标
- [ ] `docs/examples/index.html` 加 tab 切换机制, 内容按 4 tab 组织: 色卡 / 组件 / 图表 / 动效。
- [ ] 色卡 tab: 迁移现有"完整色彩规范"section (品牌色/文字层级/边框/语义状态, 明暗双模)。
- [ ] 组件 tab: 迁移现有"任务编排看板示例"+ 补充通用组件 (按钮变体/输入框/badge/card)。
- [ ] 图表 tab: 新增任务管理场景图表 (进度条/环形进度/迷你折线/状态分布条), 纯 CSS+SVG 无外部图表库。
- [ ] 动效 tab: 现有"动效规范"文字描述改为可演示实例 (悬浮/级联入场/脉冲/光晕呼吸)。
- [ ] 成功: 打开 index.html, 顶部 4 tab 可点切换, 每个 tab 内容完整可看。

## 边界
范围内:
- [ ] `docs/examples/index.html` 单文件改: 加 tab 导航 + tab panel 容器 + 切换 JS; 重组现有 section 进对应 tab; 补组件/图表/动效演示。
- [ ] 保留现有主题切换 (明暗双模)、海滩蓝金色系、glass/hover-float/animate-wave 等工具类。
- [ ] 图表用纯 CSS (进度条/状态分布) + 内联 SVG (环形/折线), 不引 chart 库。

范围外 (非目标):
- [ ] 不改 sample-skein/ 目录。
- [ ] 不改 README.md。
- [ ] 不改 webapp 真实前端 (本文件是独立 docs 样例)。
- [ ] 不引第三方图表/动效库 (保持 CDN 只有 tailwind + font-awesome)。

已知约束:
- [ ] 文件用 Tailwind CDN + font-awesome CDN, `tailwind.config` 定义 ocean/sand/night/success/warning/danger 色板 — 复用这套色。
- [ ] 单 HTML 文件, 所有 CSS/JS 内联。

## 验收标准
- [ ] 4 tab (色卡/组件/图表/动效) 可点切换, 当前 tab 高亮, 非当前隐藏。
- [ ] 色卡 tab 含原完整色彩规范 (品牌/文字/边框/状态, 明暗双模)。
- [ ] 组件 tab 含看板示例 + 按钮/输入/badge 等通用组件演示。
- [ ] 图表 tab 含 ≥3 类图表 (进度条/环形/折线或分布条), 纯 CSS+SVG。
- [ ] 动效 tab 含可演示动效实例 (非纯文字)。
- [ ] 主题切换 (明暗) 在所有 tab 生效。
- [ ] 浏览器打开无 JS 报错, tab 切换流畅。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list ui-tabs-refactor`)
