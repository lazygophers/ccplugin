# skein serve 多页管理平台重设计 — 详细设计

保后端换前端。架构 / 分波 / 关键取舍:

## 分层复用边界 (源码仓 plugins/tools/skein/)
| 层 | 现状 | 本 task |
|----|------|---------|
| serve 后端 (skein.py:1658+ serve / _build_serve_app 1797) | FastAPI, 9 endpoint + WS + exec 白名单 | **保留**, 仅新功能页时增量加 endpoint |
| 数据端点 (_dashboard/_queue/_task_detail/_spec_tree/_spec_save 1477-1963) | 已全 | **保留** |
| 前端骨架 (assets/webapp/index.html + app.js + router.js) | hash-router SPA, 7 页懒加载 | **重做** 视觉+布局, 契约 render(mount,params,ctx) 可保 |
| 样式令牌 (src/input.css oklch → dist/app.css 预构建) | 玻璃流沙双外观 | **依选定方向重做** |
| 7 页视图 (pages/*.js) | board 663 行最重 | **依选定方向重构** |

## 两波调度
**Wave A — 设计探索 (定方向)**: 3 subagent 并行 (并发上限2), 各出 1 版单文件 HTML mockup (dashboard + 1 关键页 spec/task, 假数据), huashu-design 跨度递进:
- 方向A 玻璃流沙精炼: 保现有 oklch 双外观调性根, 重构布局/信息层级 (保守锚点)。
- 方向B 标杆迁移: 迁移开发者工具标杆 dashboard 设计语言 (Linear / Vercel / Raycast 类), 换视觉。
- 方向C 定制: 为 skein「任务编织」隐喻定制的设计 (novel)。
→ main 汇总 3 版, AskUserQuestion 用户选定 1 版或混搭。**硬门: 未选不进 Wave B**。

**Wave B — 落地实现 (方向定后 subtask add 动态挂)**: 依选定方向重构真实前端 (index.html 骨架 / input.css 令牌 / 逐页 pages/*.js / nav) + 重建 dist/app.css + (新功能页则补后端 endpoint + 白名单) + 逐页启 serve 实测。

## 关键取舍
- 「保持现有风格」(原请求) vs 「换设计方向」(用户拍板) 张力 → 用 3 版跨度化解: A 锚现有调性, B/C 更换, 真实视觉里选, 不靠文字纠结。
- mockup 用假数据纯视觉, 不接后端 (探索阶段快), 选定后才接真实 ctx.api。
- 条件指令规避顶层 template fragment (recall 坑), 崩溃系统性。
- spec 保存写口 realpath 守卫是安全边界, 重构不得绕过。
