# 后端 serve 勘察 (过程证据)

## 入口链
- skein.py:2075 serve() — 持久看板入口; 读 config.yaml; monitor(auto) 遵 web_serve 开关, 手动强起。
- skein.py:2149 _run_server(open_browser, quiet) — lock 去重 (同项目复用), 随机端口, uvicorn reload。
- skein.py:2219 _build_serve_app / skein.py:3270 _serve_app_factory — uvicorn reload 子进程入口 fresh import。
- skein.py:3042 build_app(board, proj_id, quiet, on_ready) — 真正构造 FastAPI app, 返回 app。

## 常量 (DataSource seam)
- skein.py:2093-2095 _LOCK_ID_PATH="/__skein__/id", _REV_PATH="/__skein__/rev", _LIVE_PATH="/__skein__/live"。
- 多 session 去重 (_probe_same_project L2140-2147 比对项目标识) + 轮询兜底 (/rev)。

## rev 体系
- skein.py:2105-2107 _data_rev() = max mtime_ns of task.json (顶层 + 各 task)。
- skein.py:2109-2113 _asset_rev() = max mtime_ns of board 静态 + webapp 源 (rglob, vendor 二进制不纳入, 盯 dist)。
- skein.py:2115-2117 _task_json_rev() = f"{data}.{asset}" 合并 rev, /rev 轮询用。

## HTTP 端点 (build_app 内, skein.py:3119-3266)
- GET /__skein__/id :3119 → proj_id 纯文本。
- GET /__skein__/rev :3123 → 合并 rev 纯文本 (轮询兜底)。
- GET /__skein__/data :3127 → _board_data() JSON。
- GET / :3131 → HTML (webapp index.html 存在出, 否则回落 board shell)。
- GET /__skein__/dashboard :3148 → _dashboard()。
- GET /__skein__/queue :3152 → _queue()。
- GET /__skein__/task/{tid} :3156 → _task_detail() 或 404。
- GET /__skein__/spec :3161 → _spec_tree()。
- GET /__skein__/spec/file?path= :3165 → {path, content} 或 403/404。
- POST /__skein__/spec/save :3174 → {path, content} → {ok, path} 或 403/400。
- POST /__skein__/exec :3189 → {cmd, ...args} → {ok, cmd, exit, stdout, stderr} 或 403 白名单外。
- GET /__skein__/config :3206 → config() (含 ENV override)。
- POST /__skein__/config :3210 → 全量 10 键 → {ok, config} 或 400。
- GET /__skein__/archive :3229 → _archive_list()。
- GET /__skein__/search?q= :3233 → _search(q)。
- GET /task :3243, GET /board :3247 → HTML SPA fallback (_spa() L3240)。
- GET /{full_path:path} :3264 → SPA 兜底 HTML。

## 静态 mount (声明顺序硬约束, skein.py:3252-3266)
- /board → assets/board/ StaticFiles :3252
- /webapp → _NoCacheStatic(webapp/) :3255
- /src → no-cache :3256
- /dist :3257
- /vendor → StaticFiles :3258
- /task → .skein/task (规划文档 prd/design/findings.md 直出) :3261
- core `[arch] 路由声明在 mount 之前` 已遵守 (精确 /task /board @app.get 在 mount 前声明)。

## WS 协议 (skein.py:3135-3145 + _watch_loop 3070-3088)
- WS /__skein__/live: accept → clients.add → ws.receive_text() 阻塞保活 (客户端不发)。
- _watch_loop 每 500ms 比对 rev (skein.py:3075-3088):
  - cur_a != last_a (资产变) → msg="reload" 整页刷
  - cur_d != last_d (数据变) → msg="data" 软刷
  - 任一变即广播 clients send_text(msg)
- 前端 live.js:26-29 收 "reload"→location.reload, "data"→广播 subs 软刷。
- 仅 2 事件类型 (reload/data), payload 纯字符串无 schema。
- onopen 已 seen 过则 reload (服务重启, live.js:25); onclose 2s 重连, GRACE 5min 落遮罩。

## 数据源方法 (DataSource Protocol, skein.py:3013-3039)
- _board_assets_dir / _webapp_dir / _asset_rev / _data_rev / _task_json_rev / _board_data / _board_html / _webapp_html / _dashboard / _queue / _task_detail / _archive_list / _search / _spec_tree / _spec_resolve / _exec_argv / config
- 全走 _snapshot() (skein.py:1903) 单一读面; view 函数 _view_* (skein.py:2606-3005) 纯读 snap。
- 重写后端应继续满足此 Protocol (否则破 TestClient 单测面)。

## exec 白名单 (_exec_argv, skein.py:2009-2066)
- 只读: list / ready / current / doctor / status / contract / subtask-list
- 写: create / subtask-add / prd(read|write|add|check|uncheck)
- 严格 argv 列表, shell=False (core `[ops/subprocess-safety]`); subprocess.run(argv, cwd=root, capture_output=True, timeout=60) skein.py:3200。
- 前端实际仅 task 页 runRead 跑只读命令 (task.js:475 api.exec(cmd, {id}))。

## _webapp_html (skein.py:1951-1965)
- 读 assets/webapp/index.html, 填 token {{PROJ}} {{PAYLOAD}} {{VER}}。
- PAYLOAD = _board_data() JSON 内联 (首屏免往返); VER = _asset_rev (dist/app.css?v=VER 缓存击穿)。
