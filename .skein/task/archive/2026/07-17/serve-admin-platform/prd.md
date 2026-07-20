# skein serve 多页管理平台重设计 — PRD (主入口)

## 目标
重做 skein serve 前端**整套视觉 + 布局**, 保功能不减。用户对现有 7 页 SPA (玻璃流沙 oklch 双外观) 设计不满意, 要**换设计方向**。用户价值: 一个视觉更强、布局更顺手的 skein 完整管理平台 (task 面板 / 待执行队列 / prd 审阅 / spec 查看编辑 / 命令执行 / 建议新功能)。

成功长什么样:
- 先出 **3 版真实视觉 mockup** (跨度: 玻璃流沙精炼 → 标杆迁移 → 定制) 让用户选定方向 (huashu-design 选择无效铁律: 没看到视觉不定风格)。
- 依选定方向重构真实 webapp 前端 (7 页 pages/ + 样式令牌 + 导航), 后端零改动 (若加新功能页才补 endpoint)。
- 功能不回退: dashboard/queue/task/spec/archive/search/exec 全部照常工作, spec 保存仍走 realpath 守卫写口。

## 边界
**范围内**:
- 前端视觉 + 布局重设计 (`plugins/tools/skein/assets/webapp/`): index.html 骨架、样式令牌 (src/input.css → dist/app.css 预构建)、7 页 pages/*.js 视图、导航。
- 设计探索: 3 版 mockup (单文件 HTML, 假数据, 展示 dashboard + 1 关键页视觉), 用户选定 1 版或混搭。
- 新功能页 (用户勾选「新增功能页」): 依选定方向补 (memory recall 查询 / config / live 日志等, 具体待方向定后细化)。
- 命令执行入口增强: exec UI 覆盖更多 skein 命令 (白名单同步扩展)。
- petite-vue 条件指令规避顶层 template fragment 崩溃 (见已知约束)。

**范围外 (非目标)**:
- 后端 serve 骨架 / 9 数据 endpoint / WS 分级刷新 / exec 白名单机制**不推倒** (仅新增页时增量补 endpoint)。
- 旧回落看板 `assets/board/` 不动 (仅 index.html 缺失时回落)。
- 不改 skein.py 任务引擎 / task.json 结构。

**已知约束**:
- 现有前端 = vendored petite-vue + Tailwind standalone (buildless, dist/app.css 预构建入库), hash-router SPA, 页面契约 `render(mount,params,ctx)` ctx={api,md,onLive}。改样式需同步重建 dist/app.css。
- **[recall] petite-vue 顶层 v-if template fragment 崩溃** (frontend/webapp-tpl-fragment-crash-00.md): 条件指令禁放页面模板顶层, 系统性波及全部页。
- **[recall] UI 模块删除前依赖检查** (arch/webapp-drop-themes-01.md): 删/重构模块前 grep 全局使用点, 共享令牌 (oklch --bg/--accent/status 语义色) 跨页依赖须隔离保留。
- marketplace 缓存版仅旧单页 board 快照; 真值在源码仓 `plugins/tools/skein/assets/webapp/`。

## 验收标准
- [ ] 3 版 mockup 产出 (单文件 HTML 可浏览器直开), 用户选定方向。
- [ ] 依选定方向重构 index.html + 样式令牌 + 7 页视图, dist/app.css 已重建。
- [ ] 7 页功能零回退: dashboard/queue/task/spec/archive/search/exec 逐页启 serve 实测可用。
- [ ] spec 编辑保存仍走 realpath 越界守卫 (唯一写口未被绕过)。
- [ ] 条件指令无顶层 template fragment (规避 recall 崩溃坑), 整页加载不崩。
- [ ] 命令执行入口覆盖扩展的 skein 命令, exec 白名单同步 (无 shell 拼串)。
- [ ] 新功能页 (若做) 前后端联通, 数据真实。

## 索引
- 详细设计: [design.md](design.md)
- 现状架构地图: [research/webapp-architecture-map.md](research/webapp-architecture-map.md)
- 任务/子任务/调度: task.json (脚本真值, `skein subtask list serve-admin-platform`)
