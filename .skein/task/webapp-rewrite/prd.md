# 参考 examples 重写 skein serve webapp UI/UX — PRD (主入口)

## 目标
- [ ] 前端换 htm + 原生 DOM (替 petite-vue), buildless, 海滩蓝金设计系统。
- [ ] 后端 API + WS 重构 (契约重设, 配合新前端数据流)。
- [ ] 6 页信息架构重设 (导航/tab 组织参考 examples)。
- [ ] 主题简化双模 (海滩蓝金明 + 夜幕暗)。
- [ ] 成功: skein serve 跑起新 webapp, task 全生命周期操作可用, 视觉对齐 examples 海滩蓝金。

## 边界
范围内:
- [ ] `assets/webapp/` 全重写 (前端 src + index.html + tailwind.config + dist)。
- [ ] `scripts/skein.py` serve 相关端点 + WS 协议重构。
- [ ] 设计系统参考 `docs/examples/index.html` (海滩蓝金 + antd 组件 + 动效)。

范围外 (非目标):
- [ ] 不改 skein CLI 核心 (task/subtask 状态机/命令) — 仅 serve 层。
- [ ] 不改 task.json schema (数据层稳定, 仅 API 契约表述层变)。
- [ ] 不改 spec 系统。

## 验收标准
- [ ] 前端: htm + 原生 DOM, buildless (无构建步骤, ESM 直跑), 6 页全实现。
- [ ] 后端: API 端点 + WS 协议重构, serve 跑通。
- [ ] 设计: 海滩蓝金配色 + antd 组件范式 + 动效语言全落地, 明暗双模。
- [ ] 功能: task 看板/详情/队列/dashboard/archive/spec 全生命周期可操作。
- [ ] WS 实时: onLive 软刷 (或等价机制) 保留, task 状态变即刷。
- [ ] `python3 skein.py serve` 启动, 浏览器打开无 JS 报错, 各页可切。
- [ ] `python3 skein.py doctor` 通过。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (researcher 产)
- [ ] 任务/子任务/调度: task.json (脚本真值)
