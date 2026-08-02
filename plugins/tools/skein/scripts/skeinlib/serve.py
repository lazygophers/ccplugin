"""http 服务层 — `build_app` 把路由接到注入的 `DataSource`, 外加若干无状态的 serve 工具。

`build_app(board: DataSource, ...)` 不认识 `Skein`, 只认 Protocol —— 生产喂真 Skein, 测试喂
假对象经 starlette TestClient 直跑, 不开真 socket (tests/test_serve_routes.py)。

⚠️ 配置写端点 `POST /__skein__/config` 有条硬安全约束: 命中 `CFG_REMOTE_DENY` 的键一律拒写,
保留盘上原值。`hooks` 在里面 —— 它的值是 shell 命令, 远程可写 = RCE。改这段先读 docs/hooks.md §4。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import datetime
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Iterable, Optional, cast

from skeinlib.hooks.runner import debug_enabled
from skeinlib.paths import PLUGIN_ROOT, SPEC_ENTRY
from skeinlib.config import (CFG_REMOTE_DENY, CONFIG_DEFAULTS, _cfg_get_path, _coerce_config,
                             _yaml_dump, _yaml_load)
from skeinlib.views import (DataSource, _cards_signature, _spec_frontmatter, _view_archive,
                            _view_board_data, _view_dashboard, _view_queue, _view_search,
                            _view_task_detail)


def max_mtime(files: Iterable[Path]) -> str:
    return str(max((f.stat().st_mtime_ns for f in files if f.exists()), default=0))


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


def dist_dir() -> Path:
    """插件自带的前端构建产物目录 `<plugin>/assets/dist/`。

    本文件在 `<plugin>/scripts/skeinlib/` 下, 故要往上三级才到插件根。
    dist/ 是 Next.js static export 产物, 已提交到 git, 用户无需 build。"""
    return (PLUGIN_ROOT / "assets" / "dist").resolve()


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
        # 每 500ms 比 rev。资产变 (css/js/结构) → {type:"reload"} 整页刷 (换 head)。
        # 数据变 (task.json) → diff _board_data() 前后快照, 逐 task id 推 {type:"task-changed", id};
        #   无差异 (仅 mtime 变内容未变) → 兜底推 {type:"data"} (旧字符串兼容, T2 live.js dispatch 双协议)。
        # spec 变 (.skein/spec/*.md) → 推 {type:"spec-changed", path:""}; path 暂空 (spec 页全订阅, 不细粒度)。
        # ponytail: diff 范围限 status/关键字段 (不深比), O(n) n=task 数, 500ms 周期可接受 (n≤百级)。
        # 兼容: 保留字符串 "reload"/"data" (T2 live.js dispatch 兜底); 新 JSON 为主, 旧字符串作 fallback。
        last_a = board._asset_rev()
        last_d = board._data_rev()
        last_s = board._spec_rev()
        try:
            last_cards = _cards_signature(_view_board_data(board._snapshot()))
        except Exception:
            last_cards = {}

        while True:
            await asyncio.sleep(0.5)
            try:
                cur_a, cur_d, cur_s = board._asset_rev(), board._data_rev(), board._spec_rev()
            except Exception:
                continue
            msgs: list[str] = []
            if cur_a != last_a:
                msgs.append(json.dumps({"type": "reload"}))
            elif cur_d != last_d:
                # 数据变: diff task id 推精准 swap (带 card 增量, 前端可原地 patch 不必整页拉 /data);
                # 无差异兜底 "data" (全订阅软刷)。
                try:
                    board_data = _view_board_data(board._snapshot())
                    new_cards = _cards_signature(board_data)
                    card_by_id = {c["id"]: c for c in board_data.get("cards", [])}
                except Exception:
                    new_cards = {}
                    card_by_id = {}
                changed = [tid for tid, sig in new_cards.items() if last_cards.get(tid) != sig]
                # 兼容删除的 task: 旧有新无也算 changed (软刷列表移除, card 置 None 告知前端摘除)
                removed = [tid for tid in last_cards if tid not in new_cards]
                for tid in changed:
                    msgs.append(json.dumps({"type": "task-changed", "id": tid, "card": card_by_id.get(tid)}))
                for tid in removed:
                    msgs.append(json.dumps({"type": "task-changed", "id": tid, "card": None}))
                if not msgs:
                    msgs.append("data")  # 旧字符串协议兜底 (无差异但 rev 变, 全订阅软刷)
                last_cards = new_cards
            elif cur_s != last_s:
                # spec 文件变 → 推送 spec-changed 通知 (无需重建缓存, 由 spec/index.py 维护)
                msgs.append(json.dumps({"type": "spec-changed", "path": ""}))
            if msgs:
                last_a, last_d, last_s = cur_a, cur_d, cur_s
                for c in list(clients):
                    for msg in msgs:
                        try:
                            await c.send_text(msg)
                        except Exception:
                            clients.discard(c)
                            break

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

    @app.get(board._LOCK_ID_PATH, response_class=PlainTextResponse)
    async def _identify() -> str:  # 身份探测端点: 返回项目标识 (.skein 绝对路径)
        return proj_id

    @app.get(board._REV_PATH, response_class=PlainTextResponse)
    async def _rev() -> str:  # 版本探测端点: 轮询兜底 (WS 不可用时)
        return board._task_json_rev()

    @app.get("/__skein__/data")
    async def _data() -> JSONResponse:  # 看板数据端点: 前端 softRefresh / WS "data" 拉新 JSON 重渲染 (不取 HTML)
        return JSONResponse(_view_board_data(board._snapshot()))

    @app.get("/", response_class=HTMLResponse)
    async def _page() -> str:  # 首页: Next.js static export dist/index.html
        return (dist_dir() / "index.html").read_text(encoding="utf-8")

    @app.websocket(board._LIVE_PATH)
    async def _live(ws: WebSocket) -> None:  # 热重载: 接受连接后阻塞保活, rev 变时 _watch_loop 推 "reload"
        await ws.accept()
        clients.add(ws)
        try:
            while True:
                await ws.receive_text()  # 客户端不发则阻塞; 断开抛异常
        except Exception:
            pass
        finally:
            clients.discard(ws)

    # ---- Next.js 前端后端数据 endpoint (9 个; 全走 board 同一数据源) ----
    @app.get("/__skein__/dashboard")
    async def _dashboard() -> JSONResponse:  # 统计: 完成率/活跃数/subtask进度/状态分布
        return JSONResponse(_view_dashboard(board._snapshot()))

    @app.get("/__skein__/queue")
    async def _queue() -> JSONResponse:  # 待执行队列: pending subtask 队列 + task 可启动 + active 内可派发 subtask
        return JSONResponse(_view_queue(board._snapshot()))

    @app.get("/__skein__/task")  # 参数一律走 query, 禁 path 参数
    async def _task(id: str) -> Any:  # 单 task: task.json 全文 + prd/design/findings 原文 + subtask + 契约
        d = _view_task_detail(board._snapshot(), id)
        return JSONResponse(d) if d else JSONResponse({"error": "task 不存在"}, status_code=404)

    @app.get("/__skein__/spec")
    async def _spec() -> JSONResponse:  # spec 树 namespace × 类目 × 文件 (namespace 目录扫描得, 非白名单)
        return JSONResponse(board._spec_tree())

    @app.get("/__skein__/spec/meta")
    async def _spec_meta(page: int = 1, page_size: int = 20, namespace: str = "",
                         category: str = "", keyword: str = "") -> JSONResponse:
        """spec 元数据查询, 支持分页和筛选。

        Args:
            page: 页码 (从 1 开始, 默认 1)
            page_size: 每页条数 (默认 20)
            namespace: 按 namespace 筛选
            category: 按 category 筛选
            keyword: 按 keyword 模糊筛选
        """
        result = board._spec_meta(page=page, page_size=page_size,
                                  namespace=namespace, category=category, keyword=keyword)
        return JSONResponse(result)

    @app.get("/__skein__/spec/file")
    async def _spec_file(path: str) -> Any:  # 单 spec 原文 (realpath 校验限 .skein/spec/)
        p = board._spec_resolve(path)
        if p is None:
            return JSONResponse({"error": "路径越界"}, status_code=403)
        if not p.is_file():
            return JSONResponse({"error": "文件不存在"}, status_code=404)
        txt = p.read_text(encoding="utf-8", errors="replace")
        meta, body = _spec_frontmatter(txt)  # frontmatter 解析归后端; content 保留原文 (编辑器用)
        return {"path": path, "content": txt, "meta": meta, "body": body}

    def _spec_reindex() -> None:
        """spec 变更后重建索引 (index.md/backlinks.md) + spec_meta 表。

        reindex 命令会自动调用 _rebuild_spec_meta() 重建 SQLite 表, 无需额外缓存。
        """
        try:
            subprocess.run([sys.executable, str(SPEC_ENTRY), "reindex"],
                           cwd=str(board.root), capture_output=True, text=True, timeout=30)
        except Exception:
            pass  # reindex 失败不阻塞保存; watch loop 下次 tick 也会重建

    @app.post("/__skein__/spec/save")
    async def _spec_save(request: Request) -> Any:  # 写 spec (realpath 校验越界拒; 仅 .md)
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
            rel, content = body["path"], body["content"]
            assert isinstance(rel, str) and isinstance(content, str)
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None or p.suffix != ".md":
            return JSONResponse({"error": "路径越界或非 .md"}, status_code=403)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        _spec_reindex()
        return {"ok": True, "path": rel}

    @app.post("/__skein__/spec/create")
    async def _spec_create(request: Request) -> Any:  # 新建 spec 文件
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
            rel, content = body.get("path"), body.get("content", "")
            assert isinstance(rel, str) and rel.strip()
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        if not rel.endswith(".md"):
            return JSONResponse({"error": "仅支持 .md 文件"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None:
            return JSONResponse({"error": "路径越界"}, status_code=403)
        if p.exists():
            return JSONResponse({"error": "文件已存在"}, status_code=409)
        p.parent.mkdir(parents=True, exist_ok=True)
        # 默认 frontmatter + 正文骨架
        if not content.strip():
            title = p.stem
            content = f"---\ntitle: {title}\ncategory: \nkeywords: []\ninclusion: auto\n---\n\n# {title}\n\n"
        p.write_text(content, encoding="utf-8")
        _spec_reindex()
        return {"ok": True, "path": rel}

    @app.post("/__skein__/spec/delete")
    async def _spec_delete(request: Request) -> Any:  # 删除 spec 文件
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
            rel = body.get("path")
            assert isinstance(rel, str) and rel.strip()
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        p = board._spec_resolve(rel)
        if p is None or p.suffix != ".md":
            return JSONResponse({"error": "路径越界或非 .md"}, status_code=403)
        if not p.exists():
            return JSONResponse({"error": "文件不存在"}, status_code=404)
        # 禁删索引文件
        if p.name in ("index.md", "backlinks.md"):
            return JSONResponse({"error": "禁删索引文件"}, status_code=403)
        p.unlink()
        _spec_reindex()
        return {"ok": True, "path": rel}

    @app.get("/__skein__/spec/search")
    async def _spec_search(q: str) -> JSONResponse:  # 全文搜索 spec 缓存 (serve 启动时建, rev 变时重建)
        if not q.strip():
            return JSONResponse([])
        return JSONResponse(board._spec_search(q))

    @app.post("/__skein__/exec")
    def _exec(request: Request) -> Any:  # 白名单命令 (固定 argv; sync def → 跑线程池不阻塞 loop)
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        argv = board._exec_argv(body)
        if argv is None:
            return JSONResponse({"error": f"命令不在白名单: {body.get('cmd')!r}", "ok": False},
                                status_code=403)
        try:
            r = subprocess.run(argv, cwd=str(board.root), capture_output=True, text=True, timeout=60)
        except Exception as e:
            return JSONResponse({"error": str(e), "ok": False}, status_code=500)
        return {"ok": r.returncode == 0, "cmd": body.get("cmd"),
                "exit": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

    @app.post("/__skein__/finish")
    def _finish(request: Request) -> Any:  # finish 收尾: 复用 lifecycle.py finish 逻辑
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
            tid = body.get("id")
            if not isinstance(tid, str) or not tid.strip():
                return JSONResponse({"error": "id 必填"}, status_code=400)
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        try:
            r = subprocess.run([sys.executable, str(SPEC_ENTRY.parent.parent / "skein.py"), "finish", tid],
                              cwd=str(board.root), capture_output=True, text=True, timeout=60)
        except Exception as e:
            return JSONResponse({"error": str(e), "ok": False}, status_code=500)
        return {"ok": r.returncode == 0, "id": tid,
                "exit": r.returncode, "stdout": r.stdout, "stderr": r.stderr}

    @app.get("/__skein__/config")
    def _cfg_get() -> JSONResponse:  # 读 config (含 ENV override, 前端显示生效值)
        return JSONResponse(board.config())

    @app.post("/__skein__/config")
    async def _cfg_save(request: Request) -> JSONResponse:  # 写 config.yaml (只认 CONFIG_DEFAULTS 路径; 前端全量提交嵌套结构)
        # input 提交多为 str → 按叶的类型 coerce; 未知键/分组忽略 (防注入); 缺键补默认。
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)

        def _coerce(path: str, v: Any) -> Any:  # str→int/bool; 类型不合 → 默认值兜底 (不报错, 前端 debounce 全量提交)
            try:
                return _coerce_config(path, v)
            except (TypeError, ValueError):
                return _cfg_get_path(CONFIG_DEFAULTS, path)

        full: dict[str, Any] = {}
        raw_disk = _yaml_load((board.dir / "config.yaml").read_text()) if (board.dir / "config.yaml").exists() else {}
        for k, dv in CONFIG_DEFAULTS.items():
            if k in CFG_REMOTE_DENY:  # 值是 shell 命令 → 远程一律不可写, 保留盘上原值
                if k in raw_disk:
                    full[k] = raw_disk[k]
                continue
            if isinstance(dv, dict):
                group_body = body.get(k) if isinstance(body.get(k), dict) else {}
                full[k] = {gk: (_coerce(f"{k}.{gk}", group_body[gk]) if gk in group_body else gv)
                           for gk, gv in dv.items()}
            else:
                full[k] = _coerce(k, body[k]) if k in body else dv
        (board.dir / "config.yaml").write_text(_yaml_dump(full))
        return JSONResponse({"ok": True, "config": board.config()})  # 返回读回值 (含 ENV override)

    @app.get("/__skein__/archive")
    async def _archive() -> JSONResponse:  # 归档页: 已归档 + 已完成 task
        return JSONResponse(_view_archive(board._snapshot()))

    @app.get("/__skein__/trash")
    async def _trash() -> JSONResponse:  # 垃圾桶: .skein/trash/<id>.<date>/ 软删 task
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

    @app.post("/__skein__/archive/del")
    async def _archive_del(request: Request) -> JSONResponse:  # 归档 → trash (可恢复)
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        tid = body.get("id")
        if not isinstance(tid, str) or not tid.strip():
            return JSONResponse({"error": "id 必填"}, status_code=400)
        snap = board._snapshot()
        src = snap.archived_path(tid)
        if src is None or not src.exists():
            return JSONResponse({"error": f"归档任务不存在: {tid}"}, status_code=404)
        trash_dir = board.dir / "trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        dst = trash_dir / f"{tid}.{datetime.datetime.now().strftime('%Y%m%d')}"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))
        return JSONResponse({"ok": True, "moved": str(dst)})

    @app.post("/__skein__/trash/purge")
    async def _trash_purge(request: Request) -> JSONResponse:  # 永久删除 trash 中的任务
        try:
            body = json.loads(request.scope.get("skein_body") or b"{}")
        except Exception:
            return JSONResponse({"error": "bad request"}, status_code=400)
        tid = body.get("id")
        trash_dir = board.dir / "trash"
        if not trash_dir.exists():
            return JSONResponse({"error": "垃圾桶为空"}, status_code=404)
        if isinstance(tid, str) and tid.strip():
            # 删指定 task: 匹配 <id>.* 或精确目录名
            matches = [p for p in trash_dir.iterdir() if p.is_dir() and (p.name == tid or p.name.startswith(f"{tid}."))]
            if not matches:
                return JSONResponse({"error": f"垃圾桶中不存在: {tid}"}, status_code=404)
            for m in matches:
                shutil.rmtree(m)
            return JSONResponse({"ok": True, "purged": [m.name for m in matches]})
        else:
            # 清空全部
            count = 0
            for d in trash_dir.iterdir():
                if d.is_dir():
                    shutil.rmtree(d)
                    count += 1
            return JSONResponse({"ok": True, "purged_count": count})

    @app.get("/__skein__/search")
    async def _search(q: str = "") -> JSONResponse:  # 跨 task/subtask/prd/spec 关键词搜
        return JSONResponse(_view_search(board._snapshot(), q))

    # Next.js static export: dist/ 含每路由 index.html (dashboard/index.html 等)。
    # mount dist/ 为根 + html=true → 浏览器 /dashboard/ → dashboard/index.html 自然命中,
    # /dashboard (无尾斜杠) → Starlette 302 → /dashboard/ → 命中。无需逐路由声明。
    app.mount("/_next", _NoCacheStatic(directory=str(dist_dir() / "_next"), check_dir=False), name="next-static")

    # task/detail SPA 页面: 必须在 /task mount 之前, 否则被 task 数据 StaticFiles 拦截 → 404。
    # Next.js 输出 dist/task/detail/index.html, 但 /task mount 指向 .skein/task/ (数据目录)。
    @app.get("/task/detail", response_class=HTMLResponse)
    async def _spa_task_detail() -> str:
        return (dist_dir() / "task" / "detail" / "index.html").read_text(encoding="utf-8")

    # 规划文档 (prd/design/findings.md) 直出: doc.js fetch /task/<id>/<f>.md
    app.mount("/task", StaticFiles(directory=str(board.tasks), check_dir=False), name="task")
    # SPA catch-all: dist/ 根静态服务 (所有前端路由 /dashboard/ /board/ /spec/ 等的 index.html)
    # html=true → /dashboard/ 自动返回 dashboard/index.html。
    # 声明在 API + /task mount 之后 → API 优先级最高, task 文档次之, 最后 SPA。
    app.mount("/", _NoCacheStatic(directory=str(dist_dir()), html=True, check_dir=False), name="spa-root")
    return app


def _serve_app_factory() -> Any:
    # uvicorn --reload 子进程入口: fresh import skein 后由此重建 app。
    # 父进程 (_run_server) 已落 lock/开浏览器/打印, 故 on_ready=None (不在每次 reload 重跑那些)。
    from skein import Skein  # lazy: 免 serve→入口 反向 import 成环
    sk = Skein()
    quiet = os.environ.get("SKEIN_SERVE_QUIET") == "1"
    return sk._build_serve_app(str(sk.dir.resolve()), quiet, on_ready=None)
