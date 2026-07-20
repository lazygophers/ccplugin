# 重设计 skein serve 为工程化多页面管理平台 — 详细设计

## 现状 (勘察结论)
- serve = FastAPI + uvicorn, 随机端口绑 127.0.0.1, 单实例锁 `.skein/.board-server.lock`, `reload=True` 热重启
- 路由 `_build_serve_app` (`skein.py:1642-1748`): `/`=看板, `/__skein__/data`=JSON, `/__skein__/rev`, WS `/__skein__/live`, `POST /__skein__/config`, StaticFiles `/board/*` `/task/*`
- 页面 = `shell.html` + Python 填 token + 前端 `board-render.js`; 样式 `base.css`(oklch 令牌) + `themes/*.css`(10 主题)
- 数据统一 `_board_data()`; spec 在 `.skein/spec/{core,recall}/<类目>/*.md` (经 memory.py); prd 在 `.skein/task/<id>/{prd,design,findings}.md`
- **无命令执行 / spec 写 / 队列 / 归档 endpoint** — 全新面

## 工程化前端结构 `plugins/tools/skein/assets/webapp/`
```
webapp/
  index.html             # shell: 顶栏nav(7) + 全局搜索框 + <main id=view> mount + petite-vue引导
  tailwind.config.js     # oklch令牌/状态色/10主题 → Tailwind theme tokens
  src/
    input.css            # @tailwind + @layer(令牌CSS变量/主题预设/组件)
    app.js               # petite-vue app 引导 + 顶栏(nav/搜索/主题切换)
    router.js            # hash 路由: 7 route + :id 参数 + 懒加载 page 模块
    lib/
      api.js             # fetch 封装 (各 endpoint)
      md.js              # markdown 渲染 (迁移复用 doc.js 逻辑)
      live.js            # WS 热重载 (迁移复用)
    pages/
      dashboard.js  board.js  queue.js  task.js  spec.js  commands.js  archive.js
  dist/app.css           # tailwind 编译产物 (gitignore, 启动构建)
```
**vendored 运行态** (gitignore, 放 `.skein/.vendor/` 或插件 runtime cache):
- `tailwindcss` standalone 单二进制 (按 OS/arch 拉, 启动缺失自动下)
- `petite-vue.js` (启动缺失自动下)
- 启动流程: 确保二进制+petite-vue在 → 跑 `tailwindcss -i input.css -o dist/app.css --minify` → 起 serve

## 后端改动 (skein.py, 全部集中一 subtask 防冲突)
新增 endpoint:
| endpoint | 方法 | 作用 |
|---|---|---|
| `/__skein__/dashboard` | GET | 统计: 完成率/活跃数/subtask进度/状态分布 |
| `/__skein__/queue` | GET | ready task 批 + 各 task 就绪 subtask 序 (复用 ready/pop 语义) |
| `/__skein__/task/{id}` | GET | task.json + prd/design/findings 原文 + subtask + 契约 |
| `/__skein__/spec` | GET | spec 树 core/recall×类目×文件 |
| `/__skein__/spec/file` | GET | 单 spec 原文 (**realpath 校验限 .skein/spec/**) |
| `/__skein__/spec/save` | POST | 写 spec (**realpath 校验, 越界拒**) |
| `/__skein__/exec` | POST | 白名单命令 (见下), 返回 stdout/stderr/exit |
| `/__skein__/archive` | GET | 已归档 task 列表 + 详情 |
| `/__skein__/search` | GET | 跨 task/subtask/spec/prd 关键词搜 |
- serve/view 挂载点从 `board/` 改指 `webapp/` (StaticFiles `/webapp/*` + `/dist/*` + `/vendor/*`); 旧 `/board/*` 保留
- 启动 vendoring + tailwind build 钩子

**exec 白名单** (严格 enum, 非白名单拒, 固定 argv 防注入):
- 只读: `list [--status]` `ready` `pop` `current` `status [id [sid]]` `doctor` `contract <id>`查 `subtask list <id>`
- 安全写: `create <id> --name --desc` `subtask add <id> <sid> --name --desc [--deps][--agent]`
- **禁**: start/finish/archive/clean/init/setup/repos/contract --add/subtask start|done|fail

## 关键取舍
- **buildless 工程化 vs Vite**: 选 Tailwind standalone 二进制 — 无需 node/npm, 启动自足, 符合插件「python 起服务」约束 (ponytail: 不引 node 生态)
- **petite-vue vs React/Vue**: petite-vue (~6kb, 渐进式, 最接近 vanilla) — 声明式绑定够用, 复用现有资产心智
- **Tailwind config 映射 vs 保留 base.css**: 映射 — 令牌/状态色/10主题进 config, 风格一致且工程化统一, 单一来源
- **hash 路由**: 无需后端 catch-all, file:// 也可用 (虽新页依赖 http, 但路由本身兼容)
- **spec 安全**: realpath 校验 + diff 确认弹层; **exec 安全**: enum + 固定 argv, 绝不 shell 拼串
- **vendored 产物 gitignore**: tailwind 二进制/petite-vue/编译css 启动拉取构建, 不入 git

## 文件归属 (subtask 隔离, 防并发冲突)
- **s1-webapp-scaffold**: webapp/ 静态骨架 (index.html + tailwind.config.js + src/input.css)。**不碰 skein.py**。无 deps
- **s2-backend**: **全部 skein.py 改动** (9 endpoint + serve/view 挂载改 webapp + 启动 vendoring/build)。无 deps。与 s1 文件不相交, 可并行
- **s3-router-core**: webapp/src (app.js + router.js + lib/api.js + lib/md.js + lib/live.js)。dep s1,s2
- **s4~s10 页面** (各占 webapp/src/pages/ 一个文件, 互不相交, 用 tailwind utility 无共享 css 编辑):
  - s4-dashboard, s5-board(迁移看板渲染), s6-queue, s7-task(prd/design/findings+subtask+契约), s8-spec(树+编辑+diff确认), s9-commands, s10-archive。均 dep s3

## 验证
- 冷启动: 删 vendor 后起 serve, 验二进制/petite-vue 自动拉 + css 自动构建; 二启复用
- 逐页访问 + hash 直接落地; exec 白名单外命令验拒; spec 越界路径验拒; 10 主题扫一遍不破版
- git status 验 vendor/dist 未入库
- 质量门: 源码走 lint/test (非 commands/skills/agents 文档, 不需 claude -p 理解校验)
