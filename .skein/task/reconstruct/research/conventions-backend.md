# bootstrap 扫描 — backend-service + 并发/数据契约候选

mode=bootstrap · task-id=reconstruct · 纯只读。扫描主体: `plugins/tools/skein/scripts/skein.py` (2764行, FastAPI+uvicorn 本地看板服务 + task/subtask DAG 调度 + flock 并发) 及 `hooks.py` (竞态守卫)。旁证: `lib/db/adapters/sqlite.py` (数据层连接池)。所有候选每条真实 file:line, ≥2处一致才计约定, 单处标 `推测:`。层判定/取舍归 main + 用户, 下方"建议层"仅建议。

---

## 并发 / 锁

### C1
- 规则: `.skein` 状态写命令 MUST 持工作区级 `fcntl.flock` 排他锁执行 (防多进程并发 read-modify-write 破坏 task.json)。
- 证据: skein.py:99-121 (`_workspace_lock` 上下文管理器, `LOCK_EX|LOCK_NB` + 超时 SystemExit); skein.py:2751-2757 (`MUTATING` 命令集统一包锁, 纯读命令免锁)。
- 建议层: core (违反 → 并发写坏状态文件)
- 类目: arch / data

### C2
- 规则: 同一并行批禁 ≥2 个 `.skein` 状态写命令 — 必须串行 (一命令一回合) 或用 `subtask claim` 一次性认领整批。
- 证据: hooks.py:113-125 (`cmd_batch` 拦截 ≥2 写命令并 block); hooks.py:120-121 ("同写 task.json/spec 有竞态, 后写覆盖前写")。
- 建议层: core (违反 → 后写覆盖前写)
- 类目: arch / ops

### C3
- 规则: 就绪 subtask 批 MUST 一次性 claim (整批标 running), 免逐个 start 的竞态窗口。
- 证据: skein.py:1345-1364 (`claim` 全局批认领, 各 task 各 _save); skein.py:1415-1421 (`subtask claim` 整批标 running, 注释"少一轮往返 + 无竞态窗口")。
- 建议层: recall
- 类目: impl

### C4
- 规则: `started` 时刻首次置定后 MUST 不覆盖 (重认领/重启幂等)。
- 证据: skein.py:1359-1360 (claim); skein.py:1419-1420 (subtask claim); skein.py:1445-1446 (start) 均 `if not s.get("started")`。
- 建议层: recall
- 类目: impl / domain

---

## 状态持久化 / 原子写 / 增量

### C5
- 规则: per-task `task/<id>/task.json` 是单一真值源; 顶层 `.skein/task.json` 是去规范化只读镜像, 每次变更 `_sync` 重算 (不各处手工同步)。
- 证据: skein.py:222-230 (`_sync` 注释"唯一写入口...去规范化状态镜像...每次变更重算"); skein.py:268-272 (`_render_tasks` 注释"per-task 目录是真值源...顶层镜像补齐")。
- 建议层: core (违反 → 双写不一致/幽灵态)
- 类目: arch / data

### C6
- 规则: 派生/渲染文件 (task.md、顶层 task.json) 写前 MUST 先 diff, 内容未变则跳过写 (增量, 免无谓 IO/mtime 抖动)。
- 证据: skein.py:1216-1226 (`_write_if_changed` 比对后写); 调用点 skein.py:228 (顶层 task.json)、skein.py:241 (per-task task.json)。
- 建议层: recall
- 类目: impl

### C7
- 规则: `task.json` 写只走唯一入口 `_save`, 写后同步渲染子任务看板 (`_board_task`), 免各调用点漏刷。
- 证据: skein.py:238-243 (`_save` 写后调 `_board_task`, 注释"task.json 唯一写入口"); 全量 mutation (claim/subtask/start/done/fail) 均经 `self._save(t)` skein.py:1364,1390,1421,1460,1472。
- 建议层: recall
- 类目: arch / impl

### C8
- 规则: 单个 task.json 损坏 (半写/手改坏) MUST 跳过并告警, 不炸整个看板/调度。
- 证据: skein.py:254-259 (`_all` try/except JSONDecodeError 跳过损坏并 DBG.log red); skein.py:2074-2076 / 2104-2105 (读 lock JSON 亦 try/except 容错)。
- 建议层: recall
- 类目: impl

---

## soft-delete / trash / 归档

### C9
- 规则: 删 task MUST 软删入 `.skein/trash/<id>.<YYYYMMDD>/` (可恢复, 置于 task/ 外免被扫); 单 subtask 才直接移除不进 trash。
- 证据: skein.py:186 (`trash_dir` 定义 + 注释); skein.py:673 / 697-711 (`del` 软删逻辑 shutil.move 入 trash)。
- 建议层: recall
- 类目: domain

### C10
- 规则: 归档/软删移动 MUST 用 `shutil.move` (fs move 非复制), 同名目标先清旧再移 (跨平台 move 行为不一)。
- 证据: skein.py:709-711 (trash: dst.exists 先清后 move); skein.py:724 (`_archive` shutil.move)。
- 建议层: recall
- 类目: impl / ops

---

## 配置来源

### C11
- 规则: 配置真值 MUST 来自 `config.yaml` + `CONFIG_DEFAULTS` 缺键回填; ENV (`CLAUDE_PLUGIN_OPTION_*`) 覆盖优先, 禁散落硬编码。
- 证据: skein.py:149-158 (`CONFIG_DEFAULTS` 唯一默认真值源); skein.py:191-206 (`config()` 缺键回填 + ENV 覆盖); skein.py:2289-2313 (写 config 只认 CONFIG_DEFAULTS 键)。
- 建议层: core (违反 → 配置来源分裂)
- 类目: arch / ops

### C12
- 规则: 服务端口 MUST 随机探空闲 (bind :0 拿一个立即释放交 uvicorn), 禁硬编码端口。
- 证据: skein.py:2096-2101 (socket bind :0 探端口); skein.py:2117 (写 lock 记该 port)。
- 建议层: recall
- 类目: ops

---

## 路由 / mount 挂载顺序 (Starlette 声明序匹配)

### C13
- 规则: 精确 route (`/task` `/board`) MUST 在同前缀 `StaticFiles` mount **之前**声明 (Starlette 按声明顺序匹配, 否则裸路径被 mount 吞成 404)。
- 证据: skein.py:2324-2336 (显式 @app.get /task /board + 注释"显式在 mount 之前声明, Starlette 按声明顺序匹"); skein.py:2339-2348 (随后 mount /board /task)。
- 建议层: core (违反 → 页面 404)
- 类目: arch

### C14
- 规则: SPA catch-all fallback `@app.get("/{full_path:path}")` MUST 声明在所有 mount **之后** (静态先命中, 命不中才回落 index.html)。
- 证据: skein.py:2349-2353 (fallback 注释"声明在所有 mount 之后"); 位置在 2339-2348 mount 之后。
- 建议层: core (违反 → 静态资源被 SPA 吞)
- 类目: arch

### C15
- 规则: `StaticFiles` mount MUST 设 `check_dir=False` (目录未落地/未构建时不炸)。
- 证据: skein.py:2342-2348 (webapp/src/dist/vendor/task 五处 mount 均 check_dir=False)。
- 建议层: recall
- 类目: impl

### C16
- 规则: 服务内部端点路径 MUST 用 `/__skein__/` 命名空间前缀 (与用户可见路由隔离)。
- 证据: skein.py:2008-2010 (_LOCK_ID_PATH/_REV_PATH/_LIVE_PATH); skein.py:2210-2322 (data/dashboard/queue/task/spec/exec/config/archive/search 全 `/__skein__/*`)。
- 建议层: recall
- 类目: arch / style

---

## 错误响应结构 & 状态码

### C17
- 规则: HTTP 错误 MUST 返回 `JSONResponse({"error": ...}, status_code=)` — 语义码统一: 400 请求体解析失败 / 403 路径越界或白名单外 / 404 资源不存在 / 500 内部异常。
- 证据: skein.py:2242 (404 task 不存在); skein.py:2252/2267 (403 路径越界); skein.py:2264/2277/2299 (400 bad request); skein.py:2280-2281 (403 白名单外); skein.py:2285 (500 异常)。
- 建议层: core (违反 → API 契约不一致)
- 类目: impl / api

### C18
- 规则: POST body MUST 由 middleware 读一次缓存进 `request.scope["skein_body"]`, handler 复用不重读 body。
- 证据: skein.py:2185-2200 (middleware 读 body 存 scope); skein.py:2260/2275/2297 (handler 取 `request.scope.get("skein_body")`)。
- 建议层: recall
- 类目: impl

---

## 安全边界 (webapp 写/exec 端点)

### C19
- 规则: webapp 文件写/读端点 MUST 经 realpath 校验路径解析后落在允许根 (`.skein/spec/`) 内, 越界返回 403。
- 证据: skein.py:1767-1776 (`_spec_resolve` realpath 校验 `root in p.parents`); skein.py:2249-2255 (spec/file 越界 403); skein.py:2265-2267 (spec/save 越界或非 .md 403)。
- 建议层: core (违反 → 路径穿越任意读写)
- 类目: arch / security

### C20
- 规则: exec 端点 MUST 走固定 argv 命令白名单 (`_exec_argv` 逐命令构造 argv, 非白名单返回 None → 403), 禁拼接用户串成 shell。
- 证据: skein.py:1939-1986 (`_exec_argv` 白名单构造, 末尾 `return None`); skein.py:2278-2281 (None → 403); skein.py:2283 (subprocess.run argv 列表, 无 shell=True)。
- 建议层: core (违反 → 命令注入)
- 类目: arch / security

### C21
- 规则: config 写端点 MUST 只认 `CONFIG_DEFAULTS` 已知键 + 按声明类型 coerce, 未知键忽略 (防注入)。
- 证据: skein.py:2293-2313 (`_coerce` 按类型转 + `{k ... for k in CONFIG_DEFAULTS if k in body}` 只取已知键)。
- 建议层: core (违反 → 配置注入)
- 类目: security

### C22
- 规则: 白名单 exec 子进程 MUST 设 `timeout` + `cwd=root` + `capture_output`。
- 证据: skein.py:2282-2287 (subprocess.run timeout=60, cwd=board.root, capture_output=True)。
- 建议层: recall
- 类目: ops
- 信号: 弱 (单处; exec 端点唯一, 但契约明确)

---

## 分层依赖 / 框架隔离

### C23
- 规则: serve-only 重依赖 (fastapi/uvicorn/websocket) 及 atexit/socket/threading MUST 局部 import (在 serve/_run_server/factory 内), 禁模块顶层 import (缺依赖不阻塞 CLI 主流程)。
- 证据: skein.py:2067 (_run_server 内 import atexit/socket/threading/webbrowser); skein.py:2094 (import uvicorn); skein.py:2137-2139 (factory 内 from fastapi import); skein.py:2057 (_probe 内 import urllib)。
- 建议层: core (违反 → 无看板依赖时 CLI 直接 import 失败)
- 类目: arch / build

### C24
- 规则: serve 启动前缺依赖 (fastapi/uvicorn) MUST 兜底同步 pip 装, 装失败告警不静默退出。
- 证据: skein.py:2034-2045 (`_serve_deps_present` + `_install_serve_deps`); skein.py:2085-2092 (缺则装, 仍缺则 stderr 告警 return)。
- 建议层: recall
- 类目: ops

---

## 日志 / 追踪注入

### C25
- 规则: HTTP 访问日志 MUST 走 middleware 统一格式 (`ts method path -> code`, POST 附 body); monitor (非 tty, quiet) 模式静默不打印。
- 证据: skein.py:2185-2200 (middleware 统一日志 + `if not quiet`); skein.py:2004-2006 (tty 区分 quiet)。
- 建议层: recall
- 类目: ops

### C26
- 规则: 状态变更/IO 关键路径 MUST 经 `DBG.log` 注入调试追踪 (统一开关, 非裸 print)。
- 证据: skein.py:117/121 (锁获取释放); skein.py:226/258/261 (读写 task); skein.py:1221/1226 (_write_if_changed)。
- 建议层: recall
- 类目: ops

---

## 幂等 / 单例

### C27
- 规则: serve MUST 幂等去重: `.board-server.lock` 记 port, 探测命中端口的 `/__skein__/id` 比对项目标识, 同项目则复用不起第二个服务。
- 证据: skein.py:2052-2062 (`_probe_same_project` 探 /__skein__/id 比对); skein.py:2069-2083 (lock 存在且同项目 → 复用 return); skein.py:2117 (写 lock)。
- 建议层: core (违反 → 多 session 起重复服务/端口泄漏)
- 类目: ops / arch

### C28
- 规则: 退出清理 (atexit) MUST 只删本进程写的 lock (校验 lock 内 port == 本进程 port, 防误删他实例)。
- 证据: skein.py:2103-2108 (`_cleanup` 校验 port 后 unlink); skein.py:2112 (atexit.register)。
- 建议层: recall
- 类目: ops

---

## 异步 / 事件循环

### C29
- 规则: 阻塞型 handler (subprocess exec、同步 config 读) MUST 用 `sync def` (FastAPI 自动跑线程池不阻塞事件循环), 禁在 async handler 内做阻塞调用。
- 证据: skein.py:2272-2273 (_exec `def` + 注释"sync def → 跑线程池不阻塞 loop"); skein.py:2289 (_cfg_get sync def)。
- 建议层: recall
- 类目: impl

---

## 命名

### C30
- 规则: task 级状态常量 MUST 前缀 `S_`, subtask 级 MUST 前缀 `SS_` (值为中文枚举字符串)。
- 证据: skein.py:49-57 (S_PENDING/S_ACTIVE/S_CHECK/S_DONE + STATUS_ORDER); skein.py:59-61 (SS_PENDING/SS_RUNNING/SS_DONE)。
- 建议层: recall
- 类目: style

### C31
- 规则: 类内部/私有方法 MUST 前缀单下划线 (`_save`/`_load`/`_sync`/`_board`/`_run_server`/`_exec_argv`)。
- 证据: skein.py:222/232/238/245 (_sync/_load/_save/_all); skein.py:2064/1939 (_run_server/_exec_argv); 全类一致。
- 建议层: recall
- 类目: style

---

## 测试

### C32
- 规则: skein CLI 测试 MUST 经 subprocess 跑真实 skein.py + tmp 目录/git 仓 (端到端集成, 非 import 白盒)。
- 证据: test_skein.py:22-27 (subprocess.run skein.py + git init helper); test_board.py:150-162 (Popen serve + tmp 仓)。
- 建议层: recall
- 类目: test

### C33
- 规则: 锁/失败路径测试 MUST 断言 `SystemExit` / `pytest.raises` (显式验失败契约)。
- 证据: test_skein.py:249-262 (test_lock 持锁二获超时 → except SystemExit); test_board.py 相关断言。
- 建议层: recall
- 类目: test

### C34
- 规则: 看板服务集成测试 MUST 启真实 serve 子进程 + 轮询 `.board-server.lock` 取 port 再发 HTTP (非 mock)。
- 证据: test_board.py:148-162 (Popen serve + 轮询 lock port 超时断言); test_board.py:209-214。
- 建议层: recall
- 类目: test

---

## 旁证 (lib/db 数据层, 非 skein 主体 — 供 main 判是否纳入)

### C35
- 规则: 单例连接池 MUST 用 `threading.Lock` 守类级实例 + `asyncio.Lock`/`Semaphore` 守 async 初始化与池容量 (双层锁: 同步单例 + 异步并发)。
- 证据: sqlite.py:21-22 (类级 `_lock = threading.Lock()`); sqlite.py:28-30 (`asyncio.Semaphore(pool_size)` + `asyncio.Lock()`); sqlite.py:33-37 (get_instance 同步锁 double-check); sqlite.py:42-45 (initialize async 锁 double-check)。
- 建议层: recall
- 类目: arch / data
- 信号: 弱 (lib/db 是独立通用 ORM 层, 与 skein 后端无耦合; 是否属"本项目 backend 约定"需 main 判)

