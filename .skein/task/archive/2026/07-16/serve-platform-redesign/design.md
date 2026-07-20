# 重设计 skein serve 为多页面管理平台 — 详细设计

## 现状 (勘察结论)
- serve = FastAPI + uvicorn, 端口随机绑 127.0.0.1, 单实例锁 `.skein/.board-server.lock`, `reload=True` 热重启
- 路由在 `_build_serve_app` (`skein.py:1642-1748`): `/`=看板页, `/__skein__/data`=JSON, `/__skein__/rev`, WS `/__skein__/live`, `POST /__skein__/config`(改主题), StaticFiles `/board/*`(插件资产) `/task/*`(.skein/task md)
- 页面 = `shell.html` 骨架 + Python 填 token + 前端 `board-render.js` 渲染; 样式 `base.css`(令牌系统 oklch) + `themes/*.css`(10 主题)
- 数据统一 `_board_data()`; spec 在 `.skein/spec/{core,recall}/<类目>/*.md`, 经 `memory.py`; prd 在 `.skein/task/<id>/{prd,design,findings}.md`
- **无命令执行 endpoint** — 全新面

## 目标架构
**后端 (skein.py `_build_serve_app`)** 新增 endpoint:
| endpoint | 方法 | 作用 |
|---|---|---|
| `/__skein__/queue` | GET | 待执行队列: 复用 `ready`/`pop` 语义, 返回就绪 task 批 + 各 task 就绪 subtask 序 |
| `/__skein__/task/{id}` | GET | 单 task 详情: task.json + prd/design/findings md 原文 + subtask 列表 |
| `/__skein__/spec` | GET | spec 树: core/recall × 类目 × 文件 列表 |
| `/__skein__/spec/file` | GET | 单 spec 文件原文 (query: layer/category/name, **路径校验限 .skein/spec 内**) |
| `/__skein__/spec/save` | POST | 写 spec (确认后; **路径白名单校验, 拒越界**) |
| `/__skein__/exec` | POST | 执行白名单命令 (见下), 返回 stdout/stderr/exit |

**命令执行白名单** (`/__skein__/exec`, 严格 enum, 非白名单拒绝, 参数校验防注入):
- 只读: `list [--status]` `ready` `pop` `current` `status [id [sid]]` `doctor` `contract <id>`(查) `subtask list <id>`
- 安全写: `create <id> --name --desc` `subtask add <id> <sid> --name --desc [--deps] [--agent]`
- **禁**: start/finish/archive/clean/init/setup/repos/contract --add/subtask start|done|fail (碰 git/状态/worktree)
- 实现: 不走 shell 拼接, 用固定 argv 列表调 `skein.py` 或直接调内部函数

**前端 SPA (vanilla JS, 无框架)**:
- `shell.html` 加顶部 nav (5 页 tab) + 单个 `<main id=view>` 挂载点
- 新 `router.js`: hash 路由 (`#/board` `#/queue` `#/task/:id` `#/spec` `#/commands`), 切页只换 `#view` 内容, 无整页刷新; 按路由懒加载对应 page 模块
- 每页一个独立 JS (互不冲突): `board-render.js`(现有, 看板) / `page-queue.js` / `page-task.js` / `page-spec.js` / `page-commands.js`
- 每页样式内联进 `base.css` 的 `pages` 段或各自小 css; 复用令牌变量, 不引入新配色
- 现有 `switcher.js`(主题) / `doc.js`(md弹层) / `live.js`(WS) 全局保留复用

## 关键取舍
- **hash 路由 vs history 路由**: 选 hash — 无需后端 catch-all 重写, file:// 也能用, 最省改动 (ponytail)
- **服务端多页 vs 前端 SPA**: 选前端 SPA — 复用现有主题/令牌/热重载体系, 后端只加数据 endpoint
- **命令执行安全**: 白名单 enum + 固定 argv, 绝不 shell 拼串; 写命令只放 create/subtask add
- **spec 编辑安全**: 后端 `realpath` 校验落在 `.skein/spec/` 内, 保存前前端 diff 确认弹层
- **view (file://) 降级**: 新页依赖 http endpoint, file:// 静态模式下这些页显示"需 skein serve"提示, 不报错
- **第三方包**: 前端不加框架 (vanilla 够); 后端如需 diff 用 stdlib `difflib`, 不加新 dep

## 文件归属 (subtask 隔离, 防并发冲突)
- **S1 (foundation)**: `skein.py` serve 段全部新 endpoint + `shell.html` nav/挂载点 + `router.js` + `base.css` nav/通用页样式。**独占这些共享文件**, 其余 subtask 只加自己的 page JS + 读 endpoint
- **S2 待执行队列**: `page-queue.js` (+ 若需样式加 `pages/queue.css`) — dep S1
- **S3 Task/PRD 审阅**: `page-task.js` (+ `pages/task.css`) — dep S1
- **S4 Spec 查看编辑**: `page-spec.js` + diff 确认弹层 (+ `pages/spec.css`) — dep S1
- **S5 命令面板**: `page-commands.js` (+ `pages/commands.css`) — dep S1
- S1 完成后 S2-S5 文件不相交, 可并行 (上限 2)

## 验证
- 起 serve, 逐页访问 + 直接 hash 落地; 跑白名单外命令验证被拒; spec 越界路径验证被拒; 全主题扫一遍不破版
- 质量门: `claude -p` 理解校验 (CLAUDE.md 规范) 仅对 commands/skills/agents 类文档改动才需; 本 task 是源码, 走 lint/test
