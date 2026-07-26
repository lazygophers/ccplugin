# 参考 examples 重写 skein serve webapp UI/UX — 详细设计

## 决策矩阵 (grill + research 拍板锁定)
| 维度 | 决策 |
|---|---|
| 框架 | htm + 原生 DOM (2kb, 替 petite-vue, 零 vDOM/diff) |
| 构建 | **去 build-css.sh, 改 Tailwind CDN** (examples 范式, standalone binary 让步) |
| 范围 | 一次性重写 6 页 |
| 后端 | 前后端都改 (API + WS 重构) |
| 主题 | 2 套 (海滩蓝金明 + 夜幕暗, 实际现状已 2 套仅换主调) |
| 信息架构 | 重设 (hx-push-url + examples tab 组织) |
| 令牌 | **废 oklch 派生, 改 examples 16 色硬 token** (ocean5+whiteSand3+goldSand4+night3+语义3) |
| WS 粒度 | **细化 per-resource** (data-task-changed 精准 swap, 替 reload/data 二分) |
| /data 端点 | **拆片段端点** (/board/fragment + DAG 单端点 + 各页细分) |
| 路由 | **hx-push-url** (替 history pathname SPA 拦截) |

## research 关键发现 (findings.md)
- 实际 2 套主题 (非 10): skein-light :root + skein-dark。
- board 页本命令式 innerHTML (非 petite-vue, 注释拒重写) — 重写需特别处理。
- 数据面 seam = DataSource Protocol (skein.py:3013-3039) **必须保留** (_snapshot 协议, 单测依赖)。
- dag.js Sugiyama 纯函数 **勿重造** (board+task 共用, board.js:4-5 警告)。
- 15 HTTP 端点 + 6 静态 mount + WS /__skein__/live (现 reload/data 二分, 500ms 轮询 _asset_rev/_data_rev)。
- 6 页数据流: dashboard/board/queue/task/archive 有 onLive 软刷, spec 无 (编辑态保守)。

## child task DAG (researcher 建议 7 task, 已采纳)
1. **T1 设计系统落地** (无依赖先行) — examples 16 色 token + antd 组件范式 + 布局原语 + 动效, 迁进新 webapp CSS。
2. **T2 前端架构基建** (依赖 T1) — htm + 原生 DOM + hx-push-url 路由 + Tailwind CDN + 页面模块契约。
3. **T3 后端 API + WS 协议重构** (依赖 T2) — 端点拆片段 + WS per-resource + _webapp_html 调整 + 删 /vendor 加 htm。
4. **T4 board 页** (依赖 T2+T3, 保留 dag.js Sugiyama) — 命令式 innerHTML → htmx 片段。
5. **T5 dashboard+queue+archive** (依赖 T2+T3) — 三只读页 PetiteVue → htmx。
6. **T6 task+spec** (依赖 T2+T3) — task 列表/详情/DAG/exec + spec 树/编辑/diff/保存。
7. **T7 集成联调+旧码清理** (依赖 T4+T5+T6) — 6 页联调 + WS 回归 + 删旧 webapp。

## 取舍
- 全换 examples 范式: standalone binary 让步 (CDN 依赖), 换最大设计统一。
- oklch 废: 失去主题派生优雅, 换 examples 16 色直观可控。
- WS per-resource: _watch_loop + live.js 双改, 复杂度升换精准 swap 省带宽。
- 保留: DataSource Protocol + dag.js Sugiyama + task.json schema + CLI 核心 + spec 系统。

## 风险
1. 数据契约断裂 — 后端字段只加不删, 前后端同 task 同步改。
2. WS per-resource 兼容 — _watch_loop 推 + live.js 收须同步, 重连+GRACE 遮罩保留。
3. 6 页功能回归 — dag.js 勿重造, spec diff 确认 + task exec runRead + 顶栏搜索 + 配置双 Tab 易漏。
