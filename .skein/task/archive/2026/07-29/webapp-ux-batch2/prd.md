# webapp 交互批次2: 动效/面板/DAG档位/增量刷新/工时门 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 执行中状态在看板/DAG/详情上有可见动效, 一眼分辨"在跑"与"静止"。
- [ ] 看板详情面板信息结构收敛: 生命周期时间线含 exec 的 subtask 子时间线; 移除与时间线重复的"子任务列表"区块。
- [ ] task DAG 默认中号卡, 提供小/中/大三档切换; 卡片不再承担展开子 DAG 的职责 (详情面板已能看)。
- [ ] 子任务 DAG 按状态配色, 已完成置灰但保留展示 (不隐藏)。
- [ ] 进度 = task 状态机阶段与 subtask 进度的综合, 不是单纯 subtask 完成比例。
- [ ] 数据更新走 WS 增量 payload + 前端局部 patch: 刷新数据不打断用户操作 (已开的详情面板不关、滚动/选中/展开态不丢)。
- [ ] plan 阶段强制填预计工时, confirm (待处理→就绪) 校验其已更新; 工时规则作为独立 skein-flow references 存在。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: plugins/tools/skein/assets/webapp/src (board.js / task.js / app.js / lib/live.js / design.css)、scripts/skein.py (进度算法 / confirm 门 / WS 推送 payload)、skein-flow references 新文档。
- [ ] 范围外: 新前端框架或构建工具 (buildless 原生 DOM 不变)、新增第三方依赖、字体子集重生成 (图标限 icons.css 现有字形)。
- [ ] 约束: 参数一律 query 禁 path 参数; 后端 exec 白名单不放宽; python 侧改动需重启 skein serve 生效。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] 进行中 task/subtask 在卡片与 DAG 节点上有持续动效 (spinner/脉冲), 静止态无。
- [ ] 看板详情面板: 时间线 exec 节点内可展开各 subtask 子时间线; 面板内不再出现"子任务列表"区块。
- [ ] task DAG 默认中号; 档位切换含小/中/大三档且可持久化; 卡片上无"展开子任务"按钮。
- [ ] 子任务 DAG 节点按状态着色, 已完成节点灰显且仍渲染。
- [ ] `_task_pct` 综合 task 状态与 subtask 进度, python 单测覆盖 pending/ready/active/check/done × 有无 subtask 组合。
- [ ] WS 推送带资源粒度增量字段; 前端收到更新后已打开的详情面板保持打开, 选中/滚动/DAG 档位不被重置。
- [ ] 缺预计工时时 `skein.py confirm` 拒绝并给出提示; skein-flow 引用新 references 文档。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list webapp-ux-batch2`)
