#!/usr/bin/env python3
"""skein.py 看板测试 — prd checklist 渲染 + 效率不变量 (零无谓写) + serve http 面。

pytest 收集 test_*; 亦可 python3 test_board.py 直跑 (main)。

覆盖:
  1. prd_block: 解析 prd.md 目标/验收标准 两节 checklist, 跳过 TODO 占位, 进度徽标计数。
  2. 效率不变量 (用户诉求「尽可能低内存/cpu/写字节」):
     - _webapp_html() 零落盘: 不写 task.html (serve 恒实时渲染)。
     - _write_if_changed 同内容不写; 变更才写。
     - config() 键完整时不回写。
     (演进删了 _copy_board_assets / _set_config / persist 参数 — 资产改走 StaticFiles 直出,
      配置写盘走 serve POST /__skein__/config; 这些方法无对应入口可测, 已剔除断言。)
  3. serve http: 实时渲染 SPA 页 (webapp shell) + /__skein__/data 结构化端点 + 资产直出 +
     路径穿越挡 (StaticFiles 守卫) + POST 配置持久化 (源码侧 mypy 注解回归致 422, 见 skip 原因)。
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import ModuleType
from typing import Any

from conftest import SKEIN, make_ws as _init_ws, run_skein as sk  # 单一实现, 见 conftest 顶部说明
from skeinlib.views import _view_board_data
from skeinlib.store import TaskStore

_STANDALONE: bool = False  # python3 test_board.py 直跑时置 True (免 _import_pytest skip 崩 __main__)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("skein_b", SKEIN)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PRD: str = ("# PRD\n\n"
            "## 目标\n定义中立配置 schema, 作单一真值。\n- [x] 做A\n- [ ] 做B\n- [ ] TODO: 占位\n\n"
            "## 边界\n- [ ] 不动C\n\n"
            "## 验收标准\n纯文本验收也要显示。\n- [x] 过D\n- [ ] 过E\n- [ ] TODO: 占位\n")


def test_prd_and_efficiency() -> None:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _init_ws(d)
        sk(d, "create", "prd-demo", "--name", "任务一", "--desc", "d")
        (d / ".skein/task/prd-demo/prd.md").write_text(PRD)
        m = _load()
        cwd0 = os.getcwd()
        os.chdir(d)
        try:
            sk_obj = m.Skein()
            # _webapp_html() 无 persist 参数 — serve 恒实时渲染, 永不落盘 task.html
            (d / ".skein/task.html").unlink(missing_ok=True)
            html = sk_obj._webapp_html()
            # 前端迁移到 Next.js static export 后, SPA 挂载点不再有固定 id (旧 `<main id="view">`
            # 是手写 SPA 的产物); 各页面组件 (page.tsx) 统一渲染 `<main` 结构标签, 取它做挂载点存在性
            # 断言 —— 与 404 页面 (无 <main>, 见 assets/dist/404/index.html) 能明确区分。
            assert "<main" in html, "_webapp_html 应出 SPA 挂载点"

            # --- prd 数据 (前端渲染, 校验 __SKEIN__ JSON 结构而非 HTML) ---
            data = _view_board_data(sk_obj._snapshot())
            card = next(c for c in data["cards"] if c["id"] == "prd-demo")
            prd = {s["name"]: s for s in card["prd"]}
            assert set(prd) == {"目标", "验收标准"}, "prd 只应含 目标/验收标准 (边界节泄漏?)"
            assert prd["目标"]["badge"] == [1, 2], "目标徽标/计数错 (TODO 未跳过?)"
            assert prd["验收标准"]["badge"] == [1, 2], "验收标准徽标/计数错"

            def items(name: str) -> dict[str, dict[str, Any]]:
                return {i["text"]: i for i in prd[name]["items"]}
            g, a = items("目标"), items("验收标准")
            assert "TODO: 占位" not in g and "TODO: 占位" not in a, "TODO 占位未跳过 (泄漏到卡片)"
            assert g["做A"]["kind"] == "check" and g["做A"]["done"] is True, "完成项状态错"
            assert g["做B"]["kind"] == "check" and g["做B"]["done"] is False, "未完成项状态错"
            # prose 行 (无 checkbox 段落): 目标/验收标准 一致渲 todo UI — proseCls 空 (不再打 .prose 去标记)
            gp = g["定义中立配置 schema, 作单一真值。"]
            ap = a["纯文本验收也要显示。"]
            assert gp["kind"] == "prose" and gp["proseCls"] == "", "目标 prose 行应无 .prose (todo UI)"
            assert ap["kind"] == "prose" and ap["proseCls"] == "", "验收标准 prose 行应无 .prose (todo UI)"

            # --- 效率: _webapp_html() 零落盘 (实时渲染, 不写 task.html) ---
            assert not (d / ".skein/task.html").exists(), "_webapp_html() 不应落盘 task.html"

            # --- 效率: _write_if_changed 同内容不写 ---
            tp = d / ".skein/probe.txt"
            TaskStore.write_if_changed(tp, "x")
            t0 = tp.stat().st_mtime_ns
            time.sleep(0.01)
            TaskStore.write_if_changed(tp, "x")
            assert tp.stat().st_mtime_ns == t0, "_write_if_changed 同内容仍写"
            TaskStore.write_if_changed(tp, "y")
            assert tp.read_text() == "y" and tp.stat().st_mtime_ns != t0, "_write_if_changed 变更未写"

            # --- 效率: config() 键完整时不回写 ---
            cfgp = d / ".skein/config.yaml"
            sk_obj.config()  # 触发一次可能的补键回写
            c_before = cfgp.stat().st_mtime_ns
            time.sleep(0.01)
            sk_obj.config()  # 键已完整 → 不应再回写
            assert cfgp.stat().st_mtime_ns == c_before, "config() 键完整仍回写 (无谓写)"

            # --- name 为空回退 id (禁止隐藏已存在 task); 置于末尾避免 create 重落盘干扰零写断言 ---
            sk(d, "create", "no-name-task", "--name", "", "--desc", "d")
            nn = next(c for c in _view_board_data(sk_obj._snapshot())["cards"] if c["id"] == "no-name-task")
            assert nn["name"] == "no-name-task", "空 name 未回退为 id"
        finally:
            os.chdir(cwd0)


def test_serve_http() -> None:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _init_ws(d)
        sk(d, "create", "prd-demo", "--name", "任务一", "--desc", "d")
        (d / ".skein/task/prd-demo/prd.md").write_text(
            "# PRD\n## 目标\n- [x] G1\n- [ ] G2\n## 验收标准\n- [x] A1\n")
        lock = d / ".skein/.board-server.lock"
        proc = subprocess.Popen([sys.executable, str(SKEIN), "serve"], cwd=d,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            port: int | None = None
            for _ in range(100):  # 最多等 5s 拿到 lock port
                if lock.exists():
                    try:
                        port = json.loads(lock.read_text()).get("port")
                    except Exception:
                        port = None
                    if port:
                        break
                time.sleep(0.05)
            assert port, "serve 未在超时内写出 lock port"
            base = f"http://127.0.0.1:{port}"

            def get(path: str) -> tuple[int, bytes]:
                with urllib.request.urlopen(base + path, timeout=2) as r:
                    return r.status, r.read()

            # 看板页实时渲染: serve 走 Next.js static export SPA shell (dist/board/); 结构化数据走
            # /__skein__/data。旧 `/task.html` 路由随迁移消失, 看板真实页面现挂在 `/board/`
            # (dist/ 以 html=True 挂载在 "/", `/board/` 命中 dist/board/index.html)。
            st, body = get("/board/")
            b = body.decode()
            # `<main id="view">` 是旧手写 SPA 的挂载点; 迁移后各页面组件统一渲染 `<main` 结构标签
            # (assets/nextjs/src/app/board/page.tsx), 取它做挂载点存在性断言。
            assert st == 200 and "<main" in b, "serve 页缺 SPA 挂载点 (Next.js board 页)"
            st, body = get("/__skein__/data")
            card = next(c for c in json.loads(body)["cards"] if c["id"] == "prd-demo")
            prd = {s["name"]: s for s in card["prd"]}
            assert st == 200 and prd["目标"]["badge"] == [1, 2], "serve 数据端点缺 prd 徽标"
            # rev 端点: 数字串 (data_rev.asset_rev)
            st, body = get("/__skein__/rev")
            assert st == 200 and re.fullmatch(r"\d+\.\d+", body.decode()), "rev 端点格式非 data.asset 数字对"
            # 静态资产直出插件 assets/dist/ (无 .skein/ 拷贝) —— 旧 /src/design.css (手写 CSS) 已随
            # 迁移消失。改测 dist/favicon.ico: 它是 dist/ 根下确定存在的静态文件 (不像 _next/static
            # 下按 build 而变的 hash chunk, 名字固定), 走同一条 "/" 根挂载 (_NoCacheStatic html=True)
            # 直出, 足以验证「静态资产从 assets/dist/ 直出、无 .skein/ 拷贝」这条行为。
            st, body = get("/favicon.ico")
            assert st == 200 and len(body) > 0, "dist/favicon.ico 未直出"
            assert not (d / ".skein/board").exists(), "serve 误把资产拷进 .skein/"
            # 路径穿越: %2f 形式落 StaticFiles 守卫必须 404 (urllib 不折叠编码 %2f, 落守卫)
            code = 0
            try:
                get("/_next/..%2f..%2fscripts%2fskein.py")
            except urllib.error.HTTPError as e:
                code = e.code
            assert code == 404, f"路径穿越未挡 (得 {code})"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def test_serve_config_post() -> None:
    """POST /__skein__/config: 合法落盘 + 非法兜底默认值。

    commit 25dce519 给 handler 加返回注解致 FastAPI 把 `request: Request` 误解析为 query 参数
    → 422; 注解已撤回 (恢复无注解形态), POST 落盘/兜底恢复。"""
    _import_pytest()  # 仅触发可用性 (pytest 下无 skip)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _init_ws(d)
        sk(d, "create", "prd-demo", "--name", "任务一", "--desc", "d")
        lock = d / ".skein/.board-server.lock"
        proc = subprocess.Popen([sys.executable, str(SKEIN), "serve"], cwd=d,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            port = _wait_port(lock)
            assert port, "serve 未在超时内写出 lock port"
            base = f"http://127.0.0.1:{port}"

            def post(obj: dict[str, Any]) -> int:
                req = urllib.request.Request(
                    base + "/__skein__/config", data=json.dumps(obj).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=2) as r:
                        return int(r.status)
                except urllib.error.HTTPError as e:
                    return e.code

            # 合法 POST: 落盘 retain_days=30
            assert post({"retain_days": 30}) == 200, "合法 POST 应 200"
            assert "retain_days: 30" in (d / ".skein/config.yaml").read_text(), "合法值未落盘"
            # 非法 POST: 兜底为 CONFIG_DEFAULTS (retain_days=7), 不落 "not-a-number"
            assert post({"retain_days": "not-a-number"}) == 200, "非法值兜底应仍 200"
            assert "not-a-number" not in (d / ".skein/config.yaml").read_text(), "非法值误落盘"
            # 🔒 hooks 键在写端点侧硬排除 (skein.py CFG_REMOTE_DENY, 见 design.md §4): 值是 shell
            # 命令, 远程可写 = RCE。骨架本身在 CONFIG_DEFAULTS 里 (空列表), 故 "hooks" 这个串**会**
            # 出现在盘上 —— 该断言的是「POST 来的命令串一个字都不落盘」, 断言键名不出现是查错了东西。
            cfg_before = (d / ".skein/config.yaml").read_text()
            assert post({"hooks": {"agent": {"*": {"start": [
                {"type": "command", "command": "touch pwned"}]}}}}) == 200
            cfg_after = (d / ".skein/config.yaml").read_text()
            assert "touch pwned" not in cfg_after, "远程 POST 的 shell 命令落盘了 — RCE"
            assert cfg_after == cfg_before, f"hooks 段被远程改动:\n{cfg_before}\n---\n{cfg_after}"
            assert not (d / "pwned").exists()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _import_pytest() -> Any:
    try:
        import pytest as _p
        return _p
    except ImportError:
        return None  # 直跑 (python3 test_board.py) 无 pytest


def _wait_port(lock: Path, tries: int = 100) -> int | None:
    for _ in range(tries):
        if lock.exists():
            try:
                p = json.loads(lock.read_text()).get("port")
                if p:
                    return int(p)
            except Exception:
                pass
        time.sleep(0.05)
    return None


def main() -> None:
    global _STANDALONE
    _STANDALONE = True
    test_prd_and_efficiency()
    test_serve_http()
    print("skein.py 看板测试全过 (prd-checklist / 零无谓写效率不变量 / serve-http: 实时渲染·资产直出·穿越守卫)")
    # test_serve_config_post: 合法 POST 落盘 + 非法值兜底默认值。
    test_serve_config_post()


if __name__ == "__main__":
    main()
