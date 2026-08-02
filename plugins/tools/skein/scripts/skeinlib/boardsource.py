"""`DataSource` 的 Skein 侧实现 + serve 命令的生命周期编排。

`skeinlib/serve.py` 里的 `build_app` 只认 `DataSource` Protocol; 本文件是它的**生产 adapter**
(测试那个假的在 tests/test_serve_routes.py, 两个 adapter 才算真 seam)。

## 为什么是 mixin
同 doctor.py: 这些成员要读 `dir`/`tasks`/`archive_dir`/`proj`/`store`/`config()` 等十来个
`self` 属性, 且 Protocol 要求它们直接挂在喂给 `build_app` 的那个对象上。

## 依赖契约 (宿主类必须提供)
`dir` / `tasks` / `archive_dir` / `proj` / `store` / `config()` / `_wt_shown()`。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

from skeinlib.hooks.runner import DBG
from skeinlib.config import Config
from skeinlib.serve import (build_app, install_serve_deps, max_mtime, probe_same_project,
                            serve_deps_present, dist_dir)
from skeinlib.views import Snapshot
from skeinlib.paths import SCRIPTS_DIR, SKEIN_ENTRY

if TYPE_CHECKING:
    from skeinlib.task.store import TaskStore


class BoardSourceMixin:
    # 仅供 mypy 用的属性声明 (依赖契约见上方类文档字符串, 另加 `_LOCK_ID_PATH` — 门面
    # commands.py:Skein 上的类常量): 实际由宿主 Workspace/Skein 提供, TYPE_CHECKING 块运行时
    # 永不执行, 零行为改动, 只消除单看本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        dir: Path
        root: Path
        tasks: Path
        archive_dir: Path
        proj: str
        store: "TaskStore"
        _LOCK_ID_PATH: str
        _REV_PATH: str
        _LIVE_PATH: str

        def config(self) -> dict[str, Any]: ...
        def _wt_shown(self) -> bool: ...

    # ---- 看板可视化 (http 实时渲染, 不落盘; `skein.py view`/`serve` 起服务) ----
    def _snapshot(self) -> Snapshot:
        # 一次目录扫描 → 6 board 视图统一输入 (每请求构造一次)
        pools = self.config()["pools"]
        return Snapshot(
            proj=self.proj, wt_shown=self._wt_shown(),
            tasks_fn=self.store.render_tasks, all_tasks_fn=self.store.all_tasks,
            tasks_dir=self.tasks, archive_dir=self.archive_dir,
            spec_root=self._spec_root(), pool_work=pools["work"], gate_active=pools["gate"])
    def _webapp_html(self) -> str:
        # Next.js static export: 直接读 dist/index.html
        # Next.js static export: root page 做 redirect → /board, 读 board page 取 SPA entry
        board = dist_dir() / "board" / "index.html"
        if board.exists():
            return board.read_text(encoding="utf-8")
        return (dist_dir() / "index.html").read_text(encoding="utf-8")
    def _spec_rev(self) -> str:
        # spec rev: .skein/spec/ 内 .md 最大 mtime_ns。变 → WS 推 "spec-changed"。
        # ponytail: rglob ~几十 .md 文件 stat (500ms 周期, 免读内容); 与 _data_rev 独立 (spec 不进 task.json)。
        root = self._spec_root()
        if not root.exists():
            return "0"
        return max_mtime([p for p in root.rglob("*.md") if p.is_file()])
    # ---- webapp 后端数据 (serve endpoint 复用; 与 _board_data 同一数据源) ----
    def _spec_root(self) -> Path:
        return (self.dir / "spec").resolve()
    def _spec_tree(self) -> dict[str, Any]:
        """spec 树: {namespace: {category: [file, ...]}} (跳衍生索引 index.md/backlinks.md)。

        namespace 靠**目录扫描**得, 不是常量白名单 —— 与 spec.py 的 `Spec._scan_namespaces()` 同一
        判据 (design.md §2「新增 namespace 零配置」)。这里曾硬编码 `("core", "recall")`, 于是
        namespace × inclusion 改造后, 看板对 rules/product/map/external 四个真实 namespace 全盲,
        spec 树永远显示空。禁再写死清单。
        """
        root = self._spec_root()
        if not root.is_dir():
            return {}
        tree: dict[str, Any] = {}
        for ns in sorted(p for p in root.iterdir()
                         if p.is_dir() and not p.name.startswith(".")):  # 排 .archive 等衍生物
            cats: dict[str, list[str]] = {}
            for cat in sorted(p for p in ns.iterdir() if p.is_dir()):
                files = [f.name for f in sorted(cat.glob("*.md"))
                         if f.name not in ("index.md", "backlinks.md")]
                if files:
                    cats[cat.name] = files
            tree[ns.name] = cats
        return tree



    def _spec_meta(self, page: int = 1, page_size: int = 20, namespace: str = "",
                   category: str = "", keyword: str = "") -> dict[str, Any]:
        """从 SQLite 查询 spec 元数据, 支持分页和筛选。

        Args:
            page: 页码 (从 1 开始)
            page_size: 每页条数
            namespace: 按 namespace 筛选
            category: 按 category 筛选
            keyword: 按 keyword 模糊筛选

        Returns:
            dict with items (list) and total (int)
        """
        import sqlite3
        import json

        db = self._spec_root() / ".recall.db"
        if not db.exists():
            return {"items": [], "total": 0}

        con = sqlite3.connect(db)
        try:
            # 构建 WHERE 子句
            where_parts: list[str] = []
            params: list[Any] = []

            if namespace:
                where_parts.append("namespace = ?")
                params.append(namespace)
            if category:
                where_parts.append("category = ?")
                params.append(category)
            if keyword:
                where_parts.append("(title LIKE ? OR keywords LIKE ? OR path LIKE ?)")
                kw_pattern = f"%{keyword}%"
                params.extend([kw_pattern, kw_pattern, kw_pattern])

            where_clause = " AND ".join(where_parts) if where_parts else "1=1"

            # 查询总数
            count_query = f"SELECT COUNT(*) FROM spec_meta WHERE {where_clause}"
            total = con.execute(count_query, params).fetchone()[0]

            # 查询分页数据
            offset = (page - 1) * page_size
            data_query = (
                f"SELECT path, title, namespace, category, keywords FROM spec_meta "
                f"WHERE {where_clause} ORDER BY path LIMIT ? OFFSET ?"
            )
            params.extend([page_size, offset])

            rows = con.execute(data_query, params).fetchall()

            items: list[dict[str, Any]] = []
            for path, title, ns, cat, keywords_json in rows:
                try:
                    keywords = json.loads(keywords_json) if keywords_json else []
                except json.JSONDecodeError:
                    keywords = []
                items.append({
                    "path": path,
                    "title": title,
                    "namespace": ns,
                    "category": cat or "",
                    "keywords": keywords
                })

            return {"items": items, "total": total}
        finally:
            con.close()

    def _spec_search(self, q: str) -> list[dict[str, Any]]:
        """从 SQLite 全文搜索 spec, 返回匹配项。

        搜索范围: path/title/category/keywords (不含正文, 正文搜索由 FTS5 表 rules 提供)。
        """
        import sqlite3
        import json

        db = self._spec_root() / ".recall.db"
        if not db.exists():
            return []

        con = sqlite3.connect(db)
        try:
            ql = f"%{q.lower()}%"
            # 搜索 path/title/category/keywords 四个字段
            query = (
                "SELECT path, title, category, keywords FROM spec_meta "
                "WHERE LOWER(path) LIKE ? OR LOWER(title) LIKE ? OR "
                "LOWER(category) LIKE ? OR LOWER(keywords) LIKE ? "
                "ORDER BY path LIMIT 50"
            )
            rows = con.execute(query, [ql, ql, ql, ql]).fetchall()

            results: list[dict[str, Any]] = []
            for path, title, category, keywords_json in rows:
                try:
                    keywords = json.loads(keywords_json) if keywords_json else []
                except json.JSONDecodeError:
                    keywords = []

                # 生成 snippet (优先 title/keywords/category, 其次 path)
                snippet = title or " ".join(keywords) or category or path
                # 截断到 120 字符
                if len(snippet) > 120:
                    snippet = snippet[:120] + "..."

                results.append({
                    "path": path,
                    "title": title,
                    "snippet": snippet,
                    "category": category or "",
                    "keywords": keywords
                })

            return results
        finally:
            con.close()
    def _spec_resolve(self, rel: Any) -> Optional[Path]:
        # realpath 校验: 解析后必须在 .skein/spec/ 内, 越界返回 None (防路径穿越)
        root = self._spec_root()
        if not isinstance(rel, str) or not rel.strip():
            return None
        try:
            p = (root / rel).resolve()
        except Exception:
            return None
        return p if (p == root or root in p.parents) else None
    # exec 白名单: 严格 enum → 固定 argv (绝不 shell 拼串)。返回 argv 或 None(拒绝)。
    def _exec_argv(self, body: dict[str, Any]) -> Optional[list[str]]:
        cmd = body.get("cmd")
        base = [sys.executable, str(SKEIN_ENTRY)]  # 自我 re-exec 必须指入口, 不是本文件

        def s(k: str) -> Optional[str]:  # 取字符串参数; 非 str/空 → None
            v = body.get(k)
            return v.strip() if isinstance(v, str) and v.strip() else None

        def g(k: str) -> str:  # s() 的非 None 收窄版 (调用点已过 if 守卫, cast 免 mypy 误报)
            return cast(str, s(k))

        # 只读命令
        if cmd == "list":
            argv = ["list", "--json"]
            return base + (argv + ["--status", g("status")] if s("status") else argv)
        if cmd == "ready":
            return base + ["ready"]
        if cmd == "current":
            return base + ["current"]
        if cmd == "doctor":
            return base + ["doctor"]
        if cmd == "status":
            if not s("id"):
                return None
            argv = ["status", g("id")] + ([g("sid")] if s("sid") else []) + ["--json"]
            return base + argv
        if cmd == "contract":  # 仅查 (禁 --add)
            return base + ["contract", g("id")] if s("id") else None
        if cmd == "subtask-list":
            return base + ["subtask", "list", g("id")] if s("id") else None
        # 安全写命令
        if cmd == "create":
            if not (s("id") and s("name") and s("desc")):
                return None
            argv = ["create", g("id"), "--name", g("name"), "--desc", g("desc")]
            return base + (argv + ["--deps", g("deps")] if s("deps") else argv)
        if cmd == "subtask-add":
            if not (s("id") and s("sid") and s("name") and s("desc") and s("estimate")):
                return None
            argv = ["subtask", "add", g("id"), g("sid"), "--name", g("name"), "--desc", g("desc"),
                    "--estimate", g("estimate")]
            if s("deps"):
                argv += ["--deps", g("deps")]
            return base + argv
        if cmd == "clean":  # 看板「清理已完成」: 归档超 days 天的完成 task (days 仅认非负整数, 缺省 0)
            days = body.get("days", 0)
            if isinstance(days, bool) or not isinstance(days, (int, str)):
                return None
            try:
                d = int(days)
            except ValueError:
                return None
            return base + ["clean", "--days", str(d)] if d >= 0 else None
        if cmd == "confirm":
            # 看板「确认规划」按钮 = **真实用户动作**, 所以这里可以带 --approved。
            # 这是人审门最硬的一条通道: main 没有浏览器, 物理上点不了这个按钮 (对比另一条
            # 「AskUserQuestion + --approved」只靠流程纪律)。argv 固定, 不接受前端传 flag。
            # 不开 --summary 端点: 用户是在 task 详情里看着 PRD 点的按钮, 摘要已在眼前;
            # `--summary` 那个 CLI 参数仍在, 供 AskUserQuestion 通道直接跑 CLI 用。
            return base + ["confirm", g("id"), "--approved"] if s("id") else None
        if cmd == "finish":  # 看板「强制完成」: 进行中/检查中 → 已完成 (合并 worktree)
            return base + ["finish", g("id")] if s("id") else None
        if cmd == "priority":  # 看板/详情页直接改优先级 (任意状态均可改, 合法值由 CLI 侧 validate_priority 校验)
            return base + ["priority", g("id"), "--set", g("set")] if (s("id") and s("set")) else None
        if cmd == "del":  # 看板「删除任务」: 软删进 .skein/trash/ 可恢复 (仅整 task, 不开放 sid 级)
            return base + ["del", g("id")] if s("id") else None
        if cmd == "prd":  # 网页端 prd 章节编辑: read/write/add/check/uncheck (复用 CLI 同一写盘逻辑)
            if not (s("id") and s("type") and s("action")):
                return None
            act = g("action")
            if act not in ("read", "write", "add", "check", "uncheck"):
                return None
            argv = ["prd", act, g("id"), "--type", g("type")]
            if act != "read":
                if s("list") is None:
                    return None
                argv += ["--list", g("list")]
            return base + argv
        return None  # 非白名单 → 拒绝
    def view(self, _: argparse.Namespace) -> None:
        cfg = self.config()
        if not cfg["web"]["serve"]:
            print("看板 http 服务已在 config.yaml 关闭 (web.serve=false), 无法打开。", file=sys.stderr)
            return
        self._run_server(open_browser=cfg["web"]["board_open"])
    def serve(self, a: argparse.Namespace) -> None:
        # 持久看板 http 服务入口, 由 experimental.monitors (personal-scope, session 启动) + 用户手动跑维护。lock 去重: 同项目只跑一个。
        # --auto: monitor 自动起模式, 遵 config web.serve 开关 (关则 no-op)。手动跑省略 → 用户显式意图, 无视开关强起。
        auto = getattr(a, "auto", False)
        f = self.dir / "config.yaml"
        if not f.exists():
            DBG.log(f"无 .skein 工作区 ({f} 不存在) — serve 空跑退出", style="yellow")
            return  # 无 .skein 工作区 — 无 task 项目里空跑 (手动/monitor 皆退, 无盘可服务)
        cfg = Config(f).effective()  # 独立 argv 入口, 不走 self.config() (免其未初始化即报错的前置)
        if auto and not cfg["web"]["serve"]:
            DBG.log("config.yaml web.serve=false — monitor 自动起已关闭 (手动 `serve` 仍可强起)", style="yellow")
            return  # 仅 monitor 自动起遵此开关; 手动 serve 无视
        # 看板不落盘 — 页面每请求实时从 task.json 渲染 (do_GET)。
        # tty 区分: 手动终端跑 (tty) 印启动 URL 且遵 board_open 自动开浏览器; monitor 管道 (非 tty) 静默且绝不弹窗 (每 session when:always, 弹窗会骚扰)。
        # --debug 强制打印启动 URL: 非 tty 手动调试 (管道/被捕获) 也能看到服务地址, 否则误判"无法启动"; 浏览器仍只 tty 开 (非 tty 弹窗骚扰)。
        manual = sys.stdout.isatty()
        self._run_server(open_browser=manual and cfg["web"]["board_open"], quiet=not (manual or DBG.enabled))
    def _data_rev(self) -> str:
        # 数据 rev: task.json (顶层 + 各 task) 最大 mtime_ns。变 → WS 推 "data" → 软刷新只 swap .layout。
        return max_mtime([self.dir / "task.json"] + list(self.tasks.glob("*/task.json")))
    def _asset_rev(self) -> str:
        # 资产 rev: dist/ 构建产物最大 mtime_ns。变 → WS 推 "reload" → 整页 reload。
        return max_mtime([p for p in dist_dir().rglob("*") if p.is_file()])
    def _task_json_rev(self) -> str:
        # 合并 rev (data + asset): /__skein__/rev 轮询兜底端点用, 任一变即变。
        return f"{self._data_rev()}.{self._asset_rev()}"
    def _lock_file(self) -> Path:
        return self.dir / ".board-server.lock"
    def _run_server(self, open_browser: bool = True, quiet: bool = False) -> None:
        # FastAPI + uvicorn 本地看板服务 (随机 port)。热重载: WS 推 reload (rev = task.json + assets mtime)。
        # quiet=True (monitor): 不打印启动/停止行, 访问日志静默。uvicorn 自装 SIGINT/SIGTERM 优雅停机。
        import atexit, socket, threading, webbrowser, time

        lock = self._lock_file()
        log_file = self.dir / ".skein" / "serve.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        lock = self._lock_file()
        proj_id = str(self.dir.resolve())
        # 已有同项目服务在跑 → 复用, 不再起第二个 (多 session monitor 去重)。lock 失效/属别项目 → 落下方拿新随机 port 覆盖。
        if lock.exists():
            try:
                existing_port = json.loads(lock.read_text()).get("port")
            except Exception:
                existing_port = None
            if existing_port and probe_same_project(existing_port, proj_id, self._LOCK_ID_PATH):
                url = f"http://127.0.0.1:{existing_port}/"
                if not quiet:
                    print(f"SKEIN 看板服务已在运行: {url}", flush=True)
                if open_browser:
                    webbrowser.open(url)
                return

        # 依赖兜底: monitor 后台跑, 缺 fastapi/uvicorn 则同步装 (本进程非会话主线程, 不卡 session)。
        if not serve_deps_present():
            if not quiet:
                print("SKEIN 看板依赖缺失, 安装 fastapi/uvicorn 中 …", flush=True)
            install_serve_deps()
            if not serve_deps_present():
                print("SKEIN 看板依赖安装失败 — 手动 pip install -r requirements.txt", file=sys.stderr, flush=True)
                return

        import uvicorn

        # 随机空闲端口: bind :0 探一个, 立即释放交 uvicorn。
        # ponytail: close→uvicorn bind 间有 TOCTOU 窗口, 本地看板可接受; 撞了 uvicorn 抛错 monitor 重起。
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        def _cleanup() -> None:  # 退出前删 lock (仅删本进程写的, 防误删他实例)
            try:
                if lock.exists() and json.loads(lock.read_text()).get("port") == port:
                    lock.unlink()
            except Exception:
                pass

        url = f"http://127.0.0.1:{port}/"

        atexit.register(_cleanup)
        # serve 恒热重载: uvicorn reload 监视 skein.py, 改渲染码即重启 worker → 浏览器 WS 断→重连→整页刷 (WS onopen 逻辑)。
        # reload 走 import-string + factory: 子进程 fresh import skein, 需 PYTHONPATH 含脚本目录。
        # lock/浏览器/提示提前在父进程做 — on_ready 会在每次 reload 的 worker 里重跑 (重开浏览器/重写 lock), 故 factory 传 on_ready=None。
        # 资产 (css/js) 变仍由 _watch_loop 走 WS 软刷/整页刷, 不惊动 uvicorn (reload 默认只盯 *.py)。
        lock.write_text(json.dumps({"port": port, "project": proj_id}))
        if not quiet:
            print(f"SKEIN · {self.proj} 看板服务已启动: {url}  (Ctrl-C 停止, 改 skein.py 自动热重载)", flush=True)
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()

        script_dir = str(SCRIPTS_DIR)
        os.environ["PYTHONPATH"] = script_dir + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
        os.environ["SKEIN_SERVE_QUIET"] = "1" if quiet else "0"
        if DBG.enabled:
            os.environ["SKEIN_DEBUG"] = "1"  # --debug 传进 reload 子进程 (argv 不继承, 访问日志才开)

        max_retries = 3
        retry_delay = 1  # 秒，递增基数

        for attempt in range(max_retries + 1):
            try:
                # app 字符串必须与 _serve_app_factory 的**当前**所在模块一致 —— uvicorn 靠字符串
                # 在 reload 子进程里 import, 函数搬了家而字符串没跟着改, 表现是 serve 起不来
                # ("Attribute not found in module"), 且只在真起服务时才暴露。
                uvicorn.run("skeinlib.serve:_serve_app_factory", factory=True, host="127.0.0.1", port=port,
                            log_level="warning", access_log=False, reload=True, reload_dirs=[script_dir])  # 阻塞; SIGINT/SIGTERM 优雅停机
                # 正常退出（SIGINT/SIGTERM）
                break
            except SystemExit as e:
                # uvicorn 内部用 sys.exit() 退出，捕获并记录
                code = e.code if isinstance(e.code, int) else 1
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{ts}] serve exit code={code}, attempt={attempt}/{max_retries}\n"
                log_file.write_text(log_entry, encoding="utf-8")
                if code == 0 or attempt >= max_retries:
                    break
                # 非零退出且未达重试上限 → 等待递增后重启
                delay = retry_delay * (attempt + 1)
                time.sleep(delay)
            except Exception as e:
                # 其他异常（KeyboardInterrupt 除外，那是用户主动停止）
                if isinstance(e, KeyboardInterrupt):
                    break
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{ts}] serve crashed: {type(e).__name__}: {e}, attempt={attempt}/{max_retries}\n"
                log_file.write_text(log_entry, encoding="utf-8")
                if attempt >= max_retries:
                    raise
                delay = retry_delay * (attempt + 1)
                time.sleep(delay)

        if not quiet:
            print("\n看板服务已停止")
        _cleanup()
    def _build_serve_app(self, proj_id: str, quiet: bool, on_ready: Optional[Callable[[], None]] = None) -> Any:
        return build_app(self, proj_id, quiet, on_ready)  # 见模块级 build_app(DataSource seam)
