"""http 服务层 — `build_app` 把路由接到注入的 `DataSource`, 外加若干无状态的 serve 工具。

`build_app(board: DataSource, ...)` 不认识 `Skein`, 只认 Protocol —— 生产喂真 Skein, 测试喂
假对象经 starlette TestClient 直跑, 不开真 socket (tests/test_serve_routes.py)。

⚠️ 配置写端点 `POST /__skein__/system/config-set` 有条硬安全约束: hooks 段一律拒写,
保留盘上原值。它的值是 shell 命令, 远程可写 = RCE。改这段先读 docs/hooks.md §4。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import datetime
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterable, Optional, cast

from skeinlib.utils.debug import debug_enabled
from skeinlib.utils.paths import PLUGIN_ROOT, SPEC_ENTRY
from skeinlib.utils.exec_policy import SLUG_RE, exec_argv
import yaml
from skeinlib.config import Config, ConfigData
from skeinlib.web.views import (DataSource, _cards_signature, _spec_frontmatter, _view_archive,
                            _view_board_data, _view_dashboard, _view_queue, _view_search,
                            _view_task_detail)


def max_mtime(files: Iterable[Path]) -> str:
    return str(max((f.stat().st_mtime_ns for f in files if f.exists()), default=0))


# ---- 本地绑定安全闸: serve 只绑回环, Host/Origin 也只许本机名 ----------------
# 防两类攻击: ① CSRF — 恶意页面伪造 Origin 直接喷本地端口 (trash/purge rmtree、
# archive/delete、spec 覆写全是破坏端点); ② DNS rebinding — 外域解析到 127.0.0.1
# 后 Host 是攻击者域名。非本机名一律 403。
_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def _host_ok(host: str) -> bool:
    """Host 头去端口后只许 127.0.0.1 / localhost / [::1]。空 Host (HTTP/1.0) 拒。"""
    h = host.strip().lower()
    if h.startswith("["):  # IPv6 字面量 [::1]:8000
        h = h.split("]", 1)[0] + "]"
    elif ":" in h:
        h = h.rsplit(":", 1)[0]
    return h in _ALLOWED_HOSTS


def _origin_ok(origin: str) -> bool:
    """Origin (若带) 必须是 http(s)://本机名[:端口]; `null`/外域/非 http(s) 一律拒。"""
    m = re.fullmatch(r"https?://(\[[^\]]+\]|[^/:?#]+)(?::\d+)?", origin.strip().lower())
    return m is not None and _host_ok(m.group(1))


def serve_deps_present() -> bool:
    import importlib.util
    return all(importlib.util.find_spec(m) for m in ("fastapi", "uvicorn"))


def install_serve_deps() -> None:
    # serve 启动前依赖 (fastapi/uvicorn) 缺失兜底: 同步 pip 装 (本进程是后台 monitor, 不卡 session)。
    # 常规安装走 SessionStart hook 的 pip3 install -r requirements.txt, 此处仅裸装冗余保险。
    req = PLUGIN_ROOT / "requirements.txt"
    cmd = [sys.executable, "-m", "pip", "install", "-q"]
    cmd += ["-r", str(req)] if req.exists() else ["fastapi", "uvicorn[standard]"]
    subprocess.run(cmd, check=False)
# ---- Next.js static export 前端: assets/dist/ (纯静态, 无构建步骤) ----


_PLACEHOLDER = ".skein-placeholder"


def dist_dir() -> Path:
    """插件前端构建产物目录 `<plugin>/assets/dist/`。

    dist/ 是 Next.js static export 产物, 入库 (减少用户首次 build)。"""
    return (PLUGIN_ROOT / "assets" / "dist").resolve()


def pkg_manager() -> Optional[str]:
    """挑一个**真能跑**的包管理器 (pnpm 优先, 回落 yarn → npm); 都不可用返回 None。

    只看 `which` 不够: 实测过一台机器上 `which pnpm` 命中, 但那个 wrapper 指向已被删掉的
    `@pnpm/exe/pnpm`, 一跑就 exit 127。自动重编译那条路原先只探 `which`, 于是每次都选中坏的
    pnpm、每次都失败, 表现就是「改了前端没反应」——而失败信息只进了 serve 进程的 stderr。
    """
    import shutil as _sh
    for mgr in ("pnpm", "yarn", "npm"):
        if not _sh.which(mgr):
            continue
        try:
            subprocess.run([mgr, "--version"], capture_output=True, check=True, timeout=5)
            return mgr
        except (OSError, subprocess.SubprocessError):
            continue  # 装了但跑不起来 (坏 wrapper / 缺 node) —— 当没有, 试下一个
    return None


def _dist_placeholder(path: Path) -> str:
    rel = path.relative_to(dist_dir())
    return (
        "<!doctype html><meta charset=utf-8><title>SKEIN 前端未构建</title>"
        "<body style='font:14px/1.6 system-ui;padding:2rem'>"
        f"<h1>SKEIN 前端未构建</h1><p>没找到 <code>assets/dist/{rel}</code>。"
        "在插件目录跑 <code>cd assets/nextjs &amp;&amp; npm install &amp;&amp; npm run build</code>，"
        "或安装 Node.js 后重启 <code>skein board</code> 让它自动编译。</p>"
        "<p>后端接口 <code>/__skein__/*</code> 不受影响。</p>"
    )


def _read_dist_page(*parts: str) -> str:
    """static export: 按路由路径查 index.html。"""
    path = dist_dir().joinpath(*parts, "index.html")
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _dist_placeholder(path)


def _slim_dist(dd: Path) -> None:
    """build 后瘦身: 删 SVG/ico/favicon, 保留 index.html + RSC txt + _next/。

    static export 模式需要每路由 index.html (含嵌入 RSC payload), 不能删。
    """
    for item in dd.rglob("*"):
        if item.is_dir():
            continue
        if item.suffix in (".svg", ".ico"):
            item.unlink(missing_ok=True)


def ensure_dist_serveable() -> None:
    """dist/ 与 dist/_next/ 至少要存在, 否则 StaticFiles 每个请求都 500。

    `check_dir=False` 只免掉 mount 时的校验; Starlette 仍在**每次请求**里 `os.stat(directory)`,
    目录不存在就抛 `RuntimeError: StaticFiles directory ... does not exist` —— 用户看到的是
    一屏 ASGI traceback, 而不是「前端没构建」。实测发生在 marketplace 副本上 (dist/ 被
    .gitignore, 装插件时不带产物, 而那份副本的编译又失败了)。
    这里只保底不冒充成功: 补一张说明页, 让页面自己讲清楚该跑什么。
    """
    dd = dist_dir()
    (dd / "_next").mkdir(parents=True, exist_ok=True)
    index = dd / "index.html"
    if not index.is_file():
        # 标记这份 index.html 是占位而非产物, ensure_dist_built 会检测到并触发编译。
        (dd / _PLACEHOLDER).write_text("placeholder\n", encoding="utf-8")
        index.write_text(_dist_placeholder(index), encoding="utf-8")


def ensure_dist_built(quiet: bool = False) -> None:
    """dist/index.html 不存在或为占位时才编译前端; 产物入库后直接用。"""
    dd = dist_dir()
    index = dd / "index.html"
    if index.is_file() and not (dd / _PLACEHOLDER).exists():
        return  # 产物在, 跳过
    if (os.environ.get("SKEIN_NO_AUTOBUILD") == "1"
            and (dd / "index.html").is_file()
            and not (dd / _PLACEHOLDER).exists()):
        # 测试用: 套件里起 serve 只验路由, 不该被一次 40s 的前端构建拖到超时。
        # 只放过「产物在、只是过期」这一种; 产物根本没有时仍必须建 —— 否则 StaticFiles 挂上一个
        # 不存在的目录, 每个请求都抛 RuntimeError: StaticFiles directory ... does not exist。
        return
    nextjs_dir = PLUGIN_ROOT / "assets" / "nextjs"
    if not nextjs_dir.is_dir():
        raise RuntimeError("SKEIN 前端源码缺失 (assets/nextjs/), 无法自动编译")
    pkg_mgr = pkg_manager()
    if pkg_mgr is None:
        raise RuntimeError("SKEIN 自动编译需要 Node.js (npm/pnpm), 未找到可用的")
    if not quiet:
        print("SKEIN 前端首次编译中 (assets/nextjs → assets/dist) …", flush=True)

    def _retry_run(cmd: list[str], phase: str, timeout: int) -> None:
        """跑一步 install/build, 最多重试 3 次。最后一次失败才 raise。"""
        last_err = ""
        for attempt in range(1, 4):
            if not quiet:
                print(f"  [{phase}] 尝试 {attempt}/3 …", flush=True)
            try:
                subprocess.run(cmd, cwd=str(nextjs_dir),
                               capture_output=True, text=True, check=True, timeout=timeout)
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                last_err = (e.stderr or e.stdout or str(e)).strip() \
                    if isinstance(e, subprocess.CalledProcessError) else str(e)
                if attempt < 3 and not quiet:
                    print(f"  [{phase}] 失败 (attempt {attempt}), 重试中 …", flush=True)
        raise RuntimeError(f"SKEIN 前端 {phase} 失败 (3 次重试后): {last_err}")

    try:
        _retry_run([pkg_mgr, "install"], "install (依赖安装)", 300)
        _retry_run([pkg_mgr, "run", "build"], "build (编译)", 300)
        # Turbopack 禁止 distDir 跳出 projectPath → build 到 .dist/, 再移到 ../dist/
        staging = nextjs_dir / ".dist"
        if staging.is_dir():
            if dd.exists():
                shutil.rmtree(dd, ignore_errors=True)
            shutil.move(str(staging), str(dd))
            _slim_dist(dd)  # SPA 瘦身: 删掉每路由 HTML + 调试 txt
        (dd / _PLACEHOLDER).unlink(missing_ok=True)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"SKEIN 前端编译失败: {e}") from e
    if not (dd / "index.html").is_file():
        raise RuntimeError(f"SKEIN 前端编译未生成 {dd / 'index.html'}")
    (dd / _PLACEHOLDER).unlink(missing_ok=True)  # 真产物到位, 撤占位标记
    if not quiet:
        print("SKEIN 前端编译完成", flush=True)


def probe_same_project(port: int, proj_id: str, lock_id_path: str) -> bool:
    # 命中 lock 端口的 /__skein__/id, 比对项目标识。同项目→True; 连不上/不同/失效→False。
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{lock_id_path}", timeout=0.5) as r:
            return cast(bool, r.read().decode().strip() == proj_id)
    except Exception:
        return False


def build_app(board: "DataSource", proj_id: str, quiet: bool,
              on_ready: Optional[Callable[[], None]] = None) -> Any:
    # 构建 FastAPI app: 看板页实时渲染 + /board 静态直出 + 主题 POST + /__skein__/live 热重载 WS。
    from contextlib import asynccontextmanager
    from fastapi import FastAPI, Request, WebSocket
    from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    import asyncio

    # Next.js static export: dist/ 是纯静态产物, _next/ chunks 文件名含 hash 天然防缓存
    # 但 HTML 页面无 hash → no-store 强制浏览器每次都拿最新 (免 dev 迭代时看旧板)。
    class _NoCacheStatic(StaticFiles):
        async def get_response(self, path: str, scope: Any) -> Any:
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return resp

    # 注入模块全局: PEP 563 (from __future__ import annotations) 把 handler 参数注解 string化,
    # FastAPI get_typed_signature 用 handler.__globals__ (= 本模块全局) 解析 ForwardRef;
    # Request/WebSocket 仅 serve() 内局部 import → 模块全局无此名 → 解析失败 → POST request 被当 query 参数 → 422。
    # 注入模块全局后, 下面 @app.post 的参数注解 (request: Request) 解析为真类, FastAPI 正常隐式注入 Request。
    _g = globals()
    _g["Request"] = Request
    _g["WebSocket"] = WebSocket

    clients: set[Any] = set()  # 活跃热重载 WS 连接

    async def _watch_loop() -> None:
        # watchfiles (Rust 后端 notify) 事件驱动 — 监听 task 目录 + spec 目录 + 前端源码, 文件变即触发。
        # 数据变 (task.json + 文档) → 两路:
        #   (a) _cards_signature diff 命中 (status/计数/字段) → 逐 task id 推 {type:"task-changed", id, card}
        #       (card 含看板卡片全字段 + subtable, board 页 + detail 页据此增量刷新)。
        #   (b) 卡片 sig 无差异但 _task_mtimes 变 (design/findings/research 编辑) → 仍推 task-changed,
        #       card 用当前快照 (让 detail 页 load() 重拉富内容); board 卡片 sig 未变 → spread 合并是 no-op, 安全。
        #   (c) 兜底: 都无差异 (仅 mtime 变内容未变) → 推 {type:"data"} 全订阅软刷。
        # spec 变 (.skein/spec/*.md) → 推 {type:"spec-changed", path:""}; path 暂空 (spec 页全订阅, 不细粒度)。
        # 前端源码变 (assets/nextjs/src/**) → 自动 build → 推 {type:"reload"} 整页刷。
        # ponytail: diff 范围限 status/关键字段 (不深比), O(n) n=task 数, 仅事件触发时跑。
        # 兼容: 保留字符串 "reload"/"data" (T2 live.js dispatch 兜底); 新 JSON 为主, 旧字符串作 fallback。
        import watchfiles

        watch_dirs: list[Path] = [Path(str(board.tasks))]
        spec_root = Path(str(board.dir)) / "spec"
        if spec_root.exists():
            watch_dirs.append(spec_root)
        nextjs_src = PLUGIN_ROOT / "assets" / "nextjs" / "src"
        nextjs_root = PLUGIN_ROOT / "assets" / "nextjs"
        front_watch_enabled = nextjs_src.is_dir()
        if front_watch_enabled:
            watch_dirs.append(nextjs_src)

        # 前端重编译状态: build 进行中时置 True, 跳过期间的新事件 (防抖)。
        front_building = False

        try:
            last_cards = _cards_signature(_view_board_data(board._snapshot()))
        except Exception:
            last_cards = {}
        try:
            last_task_mtimes = board._task_mtimes()
        except Exception:
            last_task_mtimes = {}

        async def _push_reload() -> None:
            """前端重编译完成 → 推 reload, 浏览器整页刷拉新 dist 产物。"""
            msg = json.dumps({"type": "reload"})
            if not clients:
                return
            if debug_enabled(None):
                ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                sys.stderr.write(f"{ts} [ws] push {len(clients)} clients: reload (前端重编译)\n")
            for c in list(clients):
                try:
                    await c.send_text(msg)
                except Exception:
                    clients.discard(c)

        async def _rebuild_frontend() -> None:
            """线程池跑 next build → 成功后推 reload。"""
            nonlocal front_building
            front_building = True
            loop = asyncio.get_event_loop()
            try:
                def _do_build() -> bool:
                    pkg = pkg_manager()  # 健康探测过的, 别再用裸 which (会选中坏 wrapper)
                    if pkg is None:
                        sys.stderr.write("前端自动重编译跳过: 没有可用的 npm/pnpm\n")
                        return False
                    r = subprocess.run([pkg, "run", "build"], cwd=str(nextjs_root),
                                       capture_output=True, text=True, timeout=180)
                    if r.returncode != 0:
                        sys.stderr.write(f"前端自动重编译失败: {r.stderr[:500]}\n")
                    return r.returncode == 0

                ok = await loop.run_in_executor(None, _do_build)
                if ok:
                    sys.stderr.write(f"{datetime.datetime.now().strftime('%H:%M:%S')} [watch] frontend rebuild ok, pushing reload\n")
                    await _push_reload()
            finally:
                front_building = False

        async def _diff_and_push() -> None:
            """文件变更后: 算 card sig diff + per-task mtime diff → 推 WS。"""
            nonlocal last_cards, last_task_mtimes
            msgs: list[str] = []
            try:
                board_data = _view_board_data(board._snapshot())
                new_cards = _cards_signature(board_data)
                card_by_id = {c["id"]: c for c in board_data.get("cards", [])}
            except Exception:
                new_cards = {}
                card_by_id = {}
            changed = [tid for tid, sig in new_cards.items() if last_cards.get(tid) != sig]
            removed = [tid for tid in last_cards if tid not in new_cards]
            try:
                cur_task_mtimes = board._task_mtimes()
            except Exception:
                cur_task_mtimes = {}
            doc_changed = [tid for tid, mt in cur_task_mtimes.items()
                           if last_task_mtimes.get(tid) != mt and tid not in changed and tid not in removed]
            for tid in changed:
                msgs.append(json.dumps({"type": "task-changed", "id": tid, "card": card_by_id.get(tid)}))
            for tid in removed:
                msgs.append(json.dumps({"type": "task-changed", "id": tid, "card": None}))
            for tid in doc_changed:
                msgs.append(json.dumps({"type": "task-changed", "id": tid,
                                       "card": card_by_id.get(tid) if tid in new_cards else None}))
            if not msgs:
                msgs.append("data")  # 兜底: 无差异但文件确实变, 全订阅软刷
            last_cards = new_cards
            last_task_mtimes = cur_task_mtimes
            if msgs and clients:
                if debug_enabled(None):
                    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    sys.stderr.write(f"{ts} [ws] push {len(clients)} clients: {msgs[:3]}\n")
                for c in list(clients):
                    for msg in msgs:
                        try:
                            await c.send_text(msg)
                        except Exception:
                            clients.discard(c)

        async def _spec_changed() -> None:
            """spec 文件变更 → 推 spec-changed (无需重建缓存, 由 spec/index.py 维护)。"""
            msg = json.dumps({"type": "spec-changed", "path": ""})
            if not clients:
                return
            if debug_enabled(None):
                ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                sys.stderr.write(f"{ts} [ws] push {len(clients)} clients: {msg}\n")
            for c in list(clients):
                try:
                    await c.send_text(msg)
                except Exception:
                    clients.discard(c)

        async for changes in watchfiles.awatch(*watch_dirs):
            # changes 是 set[(change_type, path)]; 判定来源目录 → 分别路由
            any_task = any(Path(p).is_relative_to(board.tasks) for _, p in changes)
            any_spec = spec_root.exists() and any(Path(p).is_relative_to(spec_root) for _, p in changes)
            any_front = front_watch_enabled and any(Path(p).is_relative_to(nextjs_src) for _, p in changes)
            ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if any_task:
                sys.stderr.write(f"{ts} [watch] task data changed: {len(changes)} files\n")
                await _diff_and_push()
            if any_spec:
                sys.stderr.write(f"{ts} [watch] spec changed: {len(changes)} files\n")
                await _spec_changed()
            if any_front and not front_building:
                sys.stderr.write(f"{ts} [watch] frontend src changed, rebuilding...\n")
                await _rebuild_frontend()
            elif any_front and front_building:
                sys.stderr.write(f"{ts} [watch] frontend src changed but build in progress, skipped\n")

    @asynccontextmanager
    async def lifespan(_app: Any) -> AsyncIterator[None]:
        # serve 启动时无需建缓存, 数据已由 spec/index.py 的 _rebuild_spec_meta() 维护
        task = asyncio.create_task(_watch_loop())
        if on_ready:
            on_ready()  # 已 bind, 落 lock (保证 lock 在 = 端口可连)
        try:
            yield
        finally:
            task.cancel()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    # gzip: /data 实测 529KB → 123KB, design.css 74KB → 16KB。1KB 以下不压 (压缩开销 > 收益)。
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def _access_log(request: Request, call_next: Callable[[Request], Any]) -> Any:
        # 复用旧格式: ms 时间戳 + method/path -> code; POST 附 body (读一次缓存进 scope, handler 复用不重读)。
        extra = ""
        if request.method == "POST":
            try:
                raw = await request.body()
                request.scope["skein_body"] = raw
                extra = " body=" + raw.decode("utf-8", "replace")
            except Exception:
                extra = ""
        resp = await call_next(request)
        # 访问日志属 debug 级 (静态资源 200/304 刷屏无信息量): --debug / SKEIN_DEBUG 才逐条打。
        # 非 debug 只留服务端错误 (5xx) — 真问题不该被静默。
        if not quiet and (debug_enabled(None) or resp.status_code >= 500):
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            sys.stderr.write(f"{ts} {request.method} {request.url.path}{extra} -> {resp.status_code}\n")
        return resp

    @app.middleware("http")
    async def _local_guard(request: Request, call_next: Callable[[Request], Any]) -> Any:
        # 写语义请求 (POST) 的 Host/Origin 只许本机名; /__skein__/* POST 的 body
        # 强制 application/json 且必须可解析成 JSON 对象 (烂 body 400, 不让 ASGI 吐 500)。
        # OPTIONS 一律放行 (CORS 预检不带写语义)。
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.method == "POST":
            if not _host_ok(request.headers.get("host", "")):
                return JSONResponse({"error": "forbidden host", "ok": False}, status_code=403)
            origin = request.headers.get("origin")
            if origin and not _origin_ok(origin):
                return JSONResponse({"error": "forbidden origin", "ok": False}, status_code=403)
            if request.url.path.startswith("/__skein__/"):
                raw = await request.body()
                request.scope["skein_body"] = raw
                ctype = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if raw and ctype != "application/json":
                    return JSONResponse({"error": "content-type must be application/json",
                                         "ok": False}, status_code=400)
                if raw:
                    try:
                        parsed = json.loads(raw)
                    except ValueError:
                        return JSONResponse({"error": "bad json", "ok": False}, status_code=400)
                    if not isinstance(parsed, dict):
                        return JSONResponse({"error": "bad json", "ok": False}, status_code=400)
        return await call_next(request)

    # ---- 基础设施端点 (GET, 非 业务 API) ----
    @app.get(board._LOCK_ID_PATH, response_class=PlainTextResponse)
    async def _identify() -> str:  # 身份探测: 返回项目标识 (.skein 绝对路径)。probe_same_project 用 urllib GET。
        return proj_id

    @app.get(board._REV_PATH, response_class=PlainTextResponse)
    async def _rev() -> str:  # 版本探测: WS 不可用时前端轮询兜底。
        return board._task_json_rev()

    @app.get("/", response_class=HTMLResponse)
    async def _page() -> str:  # 首页: Next.js static export dist/index.html
        return _read_dist_page()

    @app.websocket(board._LIVE_PATH)
    async def _live(ws: WebSocket) -> None:  # 热重载: 接受连接后阻塞保活, rev 变时 _watch_loop 推 "reload"
        origin = ws.headers.get("origin")
        if not _host_ok(ws.headers.get("host", "")) or (origin and not _origin_ok(origin)):
            await ws.close(code=1008)  # policy violation: 非 localhost 发起的 WS 一律拒
            return
        await ws.accept()
        clients.add(ws)
        try:
            while True:
                await ws.receive_text()  # 客户端不发则阻塞; 断开抛异常
        except Exception:
            pass
        finally:
            clients.discard(ws)

    # ---- POST-only 业务端点 (语义化路径 /domain/action; 入参全走 body) ----
    def _body(request: Request) -> dict[str, Any]:
        # 烂 body (非 JSON / 非对象) 已在 _local_guard 统一 400, 这里只管取值。
        return cast(dict[str, Any], json.loads(request.scope.get("skein_body") or b"{}"))

    def _spec_reindex() -> None:
        """spec 变更后重建索引 (index.md/backlinks.md) + spec_meta 表。"""
        try:
            subprocess.run([sys.executable, str(SPEC_ENTRY), "reindex"],
                           cwd=str(board.root), capture_output=True, text=True, timeout=30)
        except Exception:
            pass

    def _run_cli(argv: list[str]) -> dict[str, Any]:
        try:
            r = subprocess.run(argv, cwd=str(board.root), capture_output=True, text=True, timeout=60)
        except Exception as e:
            return {"error": str(e), "ok": False}
        return {"ok": r.returncode == 0, "exit": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

    def _cli_from_cmd(cmd: str, body: dict[str, Any]) -> Any:
        body["cmd"] = cmd
        argv = exec_argv(body)
        if argv is None:
            return JSONResponse({"error": "参数不合法", "ok": False}, status_code=400)
        return _run_cli(argv)

    # ── 系统 ──
    @app.post("/__skein__/system/id")
    async def _system_id() -> JSONResponse:
        return JSONResponse({"path": proj_id})

    @app.post("/__skein__/system/rev")
    async def _system_rev() -> JSONResponse:
        return JSONResponse({"rev": board._task_json_rev()})

    @app.post("/__skein__/system/config-get")
    async def _config_get() -> JSONResponse:
        return JSONResponse(board.config())

    @app.post("/__skein__/system/config-set")
    async def _config_set(request: Request) -> JSONResponse:
        body = _body(request)
        # hooks 禁远程写 (值是 shell 命令 = RCE), 保留盘上原值; 其余键以盘上值为底、body 覆盖 —
        # 部分字段 POST 不许把未提及字段抹回默认值
        config = Config(board.dir / "config.yaml")
        disk = config.cfg.model_dump(by_alias=True)
        merged = {**disk, **{k: v for k, v in body.items() if k != "hooks"}}
        try:
            config._cfg = ConfigData.model_validate(merged)
        except Exception:
            # 校验失败直接 400, 不落盘 — 默认值兜底会把整份用户配置静默抹掉
            return JSONResponse({"error": "config 校验失败", "ok": False}, status_code=400)
        config._write()
        return JSONResponse({"ok": True, "config": config.cfg.model_dump(by_alias=True)})

    # ── Task ──
    @app.post("/__skein__/task/list")
    async def _task_list() -> JSONResponse:
        return JSONResponse(_view_board_data(board._snapshot()))

    @app.post("/__skein__/task/dashboard")
    async def _task_dashboard() -> JSONResponse:
        return JSONResponse(_view_dashboard(board._snapshot()))

    @app.post("/__skein__/task/queue")
    async def _task_queue() -> JSONResponse:
        return JSONResponse(_view_queue(board._snapshot()))

    @app.post("/__skein__/task/get")
    async def _task_get(request: Request) -> Any:
        body = _body(request)
        d = _view_task_detail(board._snapshot(), body.get("id", ""))
        return JSONResponse(d) if d else JSONResponse({"error": "task 不存在"}, status_code=404)

    @app.post("/__skein__/task/search")
    async def _task_search(request: Request) -> JSONResponse:
        body = _body(request)
        return JSONResponse(_view_search(board._snapshot(), body.get("q", "")))

    @app.post("/__skein__/task/create")
    def _task_create(request: Request) -> Any:
        return _cli_from_cmd("create", _body(request))

    @app.post("/__skein__/task/confirm")
    def _task_confirm(request: Request) -> Any:
        return _cli_from_cmd("confirm", _body(request))

    @app.post("/__skein__/task/revert")
    def _task_revert(request: Request) -> Any:
        return _cli_from_cmd("revert", _body(request))

    @app.post("/__skein__/task/finish")
    def _task_finish(request: Request) -> Any:
        body = _body(request)
        tid = body.get("id")
        # tid 对齐 SLUG_RE (与 design-save / exec_policy 同闸): 拒 "../" 等穿越片段
        if not isinstance(tid, str) or SLUG_RE.fullmatch(tid) is None:
            return JSONResponse({"error": "id 必填且禁路径分隔符"}, status_code=400)
        argv = [sys.executable, str(SPEC_ENTRY.parent.parent / "skein.py"), "finish", tid]
        if body.get("force") is True:
            argv.append("--force")
        result = _run_cli(argv)
        result["id"] = tid
        return result

    @app.post("/__skein__/task/priority")
    def _task_priority(request: Request) -> Any:
        return _cli_from_cmd("priority", _body(request))

    @app.post("/__skein__/task/delete")
    def _task_delete(request: Request) -> Any:
        return _cli_from_cmd("del", _body(request))

    @app.post("/__skein__/task/clean")
    def _task_clean(request: Request) -> Any:
        return _cli_from_cmd("clean", _body(request))

    @app.post("/__skein__/task/design-save")
    def _task_design_save(request: Request) -> Any:
        # design.md 全文直写 (web 端编辑详细设计, 无格式语义约束)。
        body = _body(request)
        tid, content = body.get("id"), body.get("content", "")
        # tid 对齐 SLUG_RE (kebab 字符集): 拒 "." / ".." / 路径分隔符, 从根上断路径穿越
        if not isinstance(tid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", tid):
            return JSONResponse({"error": "id 必填且禁路径分隔符"}, status_code=400)
        if not isinstance(content, str):
            return JSONResponse({"error": "bad request"}, status_code=400)
        tdir = Path(str(board.tasks)) / tid
        if not tdir.is_dir():
            return JSONResponse({"error": "task 不存在"}, status_code=404)
        (tdir / "design.md").write_text(content, encoding="utf-8")
        return {"ok": True, "id": tid}

    # ── Subtask ──
    @app.post("/__skein__/subtask/add")
    def _subtask_add(request: Request) -> Any:
        return _cli_from_cmd("subtask-add", _body(request))

    # ── Spec ──
    @app.post("/__skein__/spec/list")
    async def _spec_list() -> JSONResponse:
        return JSONResponse(board._spec_tree())

    @app.post("/__skein__/spec/meta")
    async def _spec_meta(request: Request) -> JSONResponse:
        body = _body(request)
        result = board._spec_meta(
            page=body.get("page", 1), page_size=body.get("page_size", 20),
            namespace=body.get("namespace", ""), category=body.get("category", ""),
            keyword=body.get("keyword", ""))
        return JSONResponse(result)

    @app.post("/__skein__/spec/get")
    async def _spec_get(request: Request) -> Any:
        body = _body(request)
        p = board._spec_resolve(body.get("path", ""))
        if p is None:
            return JSONResponse({"error": "路径越界"}, status_code=403)
        if not p.is_file():
            return JSONResponse({"error": "文件不存在"}, status_code=404)
        txt = p.read_text(encoding="utf-8", errors="replace")
        meta, body_text = _spec_frontmatter(txt)
        return {"path": body.get("path", ""), "content": txt, "meta": meta, "body": body_text}

    @app.post("/__skein__/spec/search")
    async def _spec_search(request: Request) -> JSONResponse:
        body = _body(request)
        q = body.get("q", "")
        if not q.strip():
            return JSONResponse([])
        return JSONResponse(board._spec_search(q))

    @app.post("/__skein__/spec/save")
    async def _spec_save(request: Request) -> Any:
        body = _body(request)
        rel, content = body.get("path"), body.get("content", "")
        if not isinstance(rel, str) or not isinstance(content, str):
            return JSONResponse({"error": "bad request"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None or p.suffix != ".md":
            return JSONResponse({"error": "路径越界或非 .md"}, status_code=403)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _spec_reindex()
        return {"ok": True, "path": rel}

    @app.post("/__skein__/spec/create")
    async def _spec_create(request: Request) -> Any:
        body = _body(request)
        rel, content = body.get("path"), body.get("content", "")
        if not isinstance(rel, str) or not rel.strip():
            return JSONResponse({"error": "bad request"}, status_code=400)
        if not rel.endswith(".md"):
            return JSONResponse({"error": "仅支持 .md 文件"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None:
            return JSONResponse({"error": "路径越界"}, status_code=403)
        if p.exists():
            return JSONResponse({"error": "文件已存在"}, status_code=409)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not content.strip():
            title = p.stem
            content = f"---\ntitle: {title}\ncategory: \nkeywords: []\ninclusion: auto\n---\n\n# {title}\n\n"
        p.write_text(content, encoding="utf-8")
        _spec_reindex()
        return {"ok": True, "path": rel}

    @app.post("/__skein__/spec/delete")
    async def _spec_delete(request: Request) -> Any:
        body = _body(request)
        rel = body.get("path")
        if not isinstance(rel, str) or not rel.strip():
            return JSONResponse({"error": "bad request"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None or p.suffix != ".md":
            return JSONResponse({"error": "路径越界或非 .md"}, status_code=403)
        if not p.exists():
            return JSONResponse({"error": "文件不存在"}, status_code=404)
        if p.name in ("index.md", "backlinks.md"):
            return JSONResponse({"error": "禁删索引文件"}, status_code=403)
        p.unlink()
        _spec_reindex()
        return {"ok": True, "path": rel}

    # ── 归档 ──
    @app.post("/__skein__/archive/list")
    async def _archive_list() -> JSONResponse:
        return JSONResponse(_view_archive(board._snapshot()))

    @app.post("/__skein__/archive/delete")
    async def _archive_delete(request: Request) -> JSONResponse:
        body = _body(request)
        tid = body.get("id")
        if not isinstance(tid, str) or SLUG_RE.fullmatch(tid) is None:
            return JSONResponse({"error": "id 必填且禁路径分隔符"}, status_code=400)
        snap = board._snapshot()
        src = snap.archived_path(tid)
        if src is None or not src.exists():
            return JSONResponse({"error": f"归档任务不存在: {tid}"}, status_code=404)
        # DataSource (views.py) 只列读面; trash 是 Workspace 的写协议, 走注入对象的实现
        dst = cast(Any, board).trash(src, tid)
        return JSONResponse({"ok": True, "moved": str(dst)})

    # ── 回收站 ──
    @app.post("/__skein__/trash/list")
    async def _trash_list() -> JSONResponse:
        trash_dir = board.dir / "trash"
        tasks: list[dict[str, Any]] = []
        if trash_dir.exists():
            for d in sorted(trash_dir.iterdir()):
                if not d.is_dir():
                    continue
                tj = d / "task.json"
                info: dict[str, Any] = {"id": d.name, "name": d.name, "status": "deleted"}
                if tj.exists():
                    try:
                        t = json.loads(tj.read_text())
                        info = {"id": t.get("id", d.name), "name": t.get("name", d.name),
                                "status": t.get("status", "deleted"), "desc": t.get("desc", ""),
                                "deletedAt": d.name}
                    except Exception:
                        pass
                tasks.append(info)
        return JSONResponse({"tasks": tasks})

    @app.post("/__skein__/trash/purge")
    async def _trash_purge(request: Request) -> JSONResponse:
        body = _body(request)
        tid = body.get("id")
        trash_dir = board.dir / "trash"
        if not trash_dir.exists():
            return JSONResponse({"error": "垃圾桶为空"}, status_code=404)
        if isinstance(tid, str) and tid.strip():
            if SLUG_RE.fullmatch(tid) is None:
                return JSONResponse({"error": "id 必填且禁路径分隔符"}, status_code=400)
            # 整名精确匹配 <tid> 或 <tid>.<YYYYMMDD> — 前缀匹配会让 tid=a 误删 a.* 任意后缀目录
            pat = re.compile(re.escape(tid) + r"\.\d{8}")
            matches = [p for p in trash_dir.iterdir()
                       if p.is_dir() and (p.name == tid or pat.fullmatch(p.name) is not None)]
            if not matches:
                return JSONResponse({"error": f"垃圾桶中不存在: {tid}"}, status_code=404)
            for m in matches:
                shutil.rmtree(m)
            return JSONResponse({"ok": True, "purged": [m.name for m in matches]})
        count = 0
        for d in trash_dir.iterdir():
            if d.is_dir():
                shutil.rmtree(d)
                count += 1
        return JSONResponse({"ok": True, "purged_count": count})

    # static export: 每路由有 index.html, mount dist/ 为根 + html=true。
    ensure_dist_serveable()
    app.mount("/_next", _NoCacheStatic(directory=str(dist_dir() / "_next"), check_dir=False), name="next-static")

    @app.get("/task/detail", response_class=HTMLResponse)
    @app.get("/task/detail/", response_class=HTMLResponse)
    async def _spa_task_detail() -> str:
        return _read_dist_page("task", "detail")

    # 规划文档 (prd/design/findings.md) 直出: doc.js fetch /task/<id>/<f>.md
    app.mount("/task", StaticFiles(directory=str(board.tasks), check_dir=False), name="task")
    # static export: dist/ 每路由 index.html, mount 为根 + html=true。
    # /dashboard/ → dashboard/index.html; /dashboard → 302 → /dashboard/ → 命中。
    app.mount("/", _NoCacheStatic(directory=str(dist_dir()), html=True, check_dir=False), name="spa-root")
    return app


def _serve_app_factory() -> Any:
    # uvicorn --reload 子进程入口: fresh import skein 后由此重建 app。
    # 父进程 (_run_server) 已落 lock/开浏览器/打印, 故 on_ready=None (不在每次 reload 重跑那些)。
    from skein import Skein  # lazy: 免 serve→入口 反向 import 成环
    sk = Skein()
    quiet = os.environ.get("SKEIN_SERVE_QUIET") == "1"
    return sk._build_serve_app(str(sk.dir.resolve()), quiet, on_ready=None)
