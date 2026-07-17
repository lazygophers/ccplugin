#!/usr/bin/env python3
"""skein.py 看板测试 — prd checklist 渲染 + 效率不变量 (零无谓写 / 低 cpu) + serve http 面。

无框架, 纯 assert。跑: python3 test_board.py

覆盖:
  1. prd_block: 解析 prd.md 目标/验收标准 两节 checklist, 跳过 TODO 占位, 进度徽标计数。
  2. 效率不变量 (用户诉求「尽可能低内存/cpu/写字节」):
     - serve 渲染 (persist=False) 零落盘: 不写 task.html, 不拷 .skein/board/。
     - _copy_board_assets 幂等: 二次拷贝不触碰任何 mtime (免无谓写)。
     - _write_if_changed 同内容不写; 变更才写。
     - _set_config 同值 no-op 不写; 变更才写; 非白名单键拒。
     - config() 键完整时不回写。
  3. serve http: 实时渲染页含 prd、静态资产直出插件(不拷)、路径穿越挡、POST 改配置落盘/非法兜底默认值。
"""
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

SKEIN = Path(__file__).parent / "skein.py"


def sk(cwd, *args, check=True):
    return subprocess.run([sys.executable, str(SKEIN), *args], cwd=cwd,
                          capture_output=True, text=True, check=check)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _load():
    spec = importlib.util.spec_from_file_location("skein_b", SKEIN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _init_ws(d):
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t.dev")
    git(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("s\n")
    git(d, "add", "-A")
    git(d, "commit", "-qm", "seed")
    sk(d, "init")


def _mtimes(root):
    return {p: p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}


PRD = ("# PRD\n\n"
       "## 目标\n定义中立配置 schema, 作单一真值。\n- [x] 做A\n- [ ] 做B\n- [ ] TODO: 占位\n\n"
       "## 边界\n- [ ] 不动C\n\n"
       "## 验收标准\n纯文本验收也要显示。\n- [x] 过D\n- [ ] 过E\n- [ ] TODO: 占位\n")


def test_prd_and_efficiency():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_ws(d)
        sk(d, "create", "prd-demo", "--name", "任务一", "--desc", "d")
        (d / ".skein/task/prd-demo/prd.md").write_text(PRD)
        m = _load()
        cwd0 = os.getcwd()
        os.chdir(d)
        try:
            sk_obj = m.Skein()
            # create 已落 task.html + board/; 先清掉, 才能验 persist=False 不重建
            (d / ".skein/task.html").unlink(missing_ok=True)
            import shutil
            shutil.rmtree(d / ".skein/board", ignore_errors=True)
            html = sk_obj._board_html(persist=False)

            # --- prd 数据 (前端渲染, 校验 __SKEIN__ JSON 结构而非 HTML) ---
            data = sk_obj._board_data()
            card = next(c for c in data["cards"] if c["id"] == "prd-demo")
            prd = {s["name"]: s for s in card["prd"]}
            assert set(prd) == {"目标", "验收标准"}, "prd 只应含 目标/验收标准 (边界节泄漏?)"
            assert prd["目标"]["badge"] == [1, 2], "目标徽标/计数错 (TODO 未跳过?)"
            assert prd["验收标准"]["badge"] == [1, 2], "验收标准徽标/计数错"

            def items(name):
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

            # --- 效率: serve 渲染零落盘 ---
            assert not (d / ".skein/task.html").exists(), "serve 渲染 (persist=False) 不应落盘 task.html"
            assert not (d / ".skein/board").exists(), "serve 渲染不应拷 board 资产到 .skein/"

            # --- 效率: _copy_board_assets 幂等 (二拷零改 mtime) ---
            sk_obj._copy_board_assets()
            board = d / ".skein/board"
            assert board.exists(), "首次拷贝未建 board/"
            mt1 = _mtimes(board)
            time.sleep(0.01)
            sk_obj._copy_board_assets()
            mt2 = _mtimes(board)
            assert mt1 == mt2, "二次拷贝触碰了 mtime (无谓写)"

            # --- 效率: _write_if_changed 同内容不写 ---
            tp = d / ".skein/probe.txt"
            m.Skein._write_if_changed(tp, "x")
            t0 = tp.stat().st_mtime_ns
            time.sleep(0.01)
            m.Skein._write_if_changed(tp, "x")
            assert tp.stat().st_mtime_ns == t0, "_write_if_changed 同内容仍写"
            m.Skein._write_if_changed(tp, "y")
            assert tp.read_text() == "y" and tp.stat().st_mtime_ns != t0, "_write_if_changed 变更未写"

            # --- 效率: config() 键完整时不回写 ---
            cfgp = d / ".skein/config.yaml"
            sk_obj.config()  # 触发一次可能的补键回写
            c_before = cfgp.stat().st_mtime_ns
            time.sleep(0.01)
            cur = sk_obj.config().get("retain_days")
            assert cfgp.stat().st_mtime_ns == c_before, "config() 键完整仍回写 (无谓写)"

            # --- 效率: _set_config 同值 no-op / 变更才写 / 非白名单拒 ---
            c0 = cfgp.stat().st_mtime_ns
            time.sleep(0.01)
            assert sk_obj._set_config("retain_days", cur) is False, "_set_config 同值应 no-op 返 False"
            assert cfgp.stat().st_mtime_ns == c0, "_set_config 同值仍写"
            newt = (cur + 1) if cur != 7 else 8
            assert sk_obj._set_config("retain_days", newt) is True, "_set_config 变更应写返 True"
            assert m._yaml_load(cfgp.read_text())["retain_days"] == newt, "_set_config 未落盘新值"
            assert sk_obj._set_config("evil_key", 1) is False, "非白名单键应拒写"
            assert "evil_key" not in m._yaml_load(cfgp.read_text()), "非白名单键泄漏进 config"

            # --- name 为空回退 id (禁止隐藏已存在 task); 置于末尾避免 create 重落盘干扰零写断言 ---
            sk(d, "create", "no-name-task", "--name", "", "--desc", "d")
            nn = next(c for c in sk_obj._board_data()["cards"] if c["id"] == "no-name-task")
            assert nn["name"] == "no-name-task", "空 name 未回退为 id"
        finally:
            os.chdir(cwd0)


def test_serve_http():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        _init_ws(d)
        sk(d, "create", "prd-demo", "--name", "任务一", "--desc", "d")
        (d / ".skein/task/prd-demo/prd.md").write_text(
            "# PRD\n## 目标\n- [x] G1\n- [ ] G2\n## 验收标准\n- [x] A1\n")
        # create 已落 board/; 清掉才能验 serve(http) 直出资产、不回拷 .skein/board/
        import shutil
        shutil.rmtree(d / ".skein/board", ignore_errors=True)
        lock = d / ".skein/.board-server.lock"
        proc = subprocess.Popen([sys.executable, str(SKEIN), "serve"], cwd=d,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            port = None
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

            def get(path):
                with urllib.request.urlopen(base + path, timeout=2) as r:
                    return r.status, r.read()

            # 看板页实时渲染: shell + 内联 window.__SKEIN__ (前端渲染, 结构数据走 /__skein__/data)
            st, body = get("/task.html")
            b = body.decode()
            assert st == 200 and "window.__SKEIN__" in b, "serve 页缺内联看板数据"
            st, body = get("/__skein__/data")
            card = next(c for c in json.loads(body)["cards"] if c["id"] == "prd-demo")
            prd = {s["name"]: s for s in card["prd"]}
            assert st == 200 and prd["目标"]["badge"] == [1, 2], "serve 数据端点缺 prd 徽标"
            # rev 端点: 数字串 (mtime_ns)
            st, body = get("/__skein__/rev")
            assert st == 200 and re.fullmatch(r"\d+\.\d+", body.decode()), "rev 端点格式非 data.asset 数字对"
            # 静态资产直出插件 assets, 且 serve 不拷 .skein/board/
            st, body = get("/board/base.css")
            assert st == 200 and b".prd" in body, "board/base.css 未直出或缺 .prd 样式"
            assert not (d / ".skein/board").exists(), "serve 误把 board 资产拷进 .skein/"
            # 路径穿越: 解析到 assets 外的真实文件也必须 404 (startswith 守卫)
            code = 0
            try:
                get("/board/../../scripts/skein.py")
            except urllib.error.HTTPError as e:
                code = e.code
            assert code == 404, f"路径穿越未挡 (得 {code})"
            # POST 改配置: 合法落盘, 非法 (未知键 / 类型不合) 不改有效值
            def post(obj):
                req = urllib.request.Request(
                    base + "/__skein__/config", data=json.dumps(obj).encode(),
                    headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=2) as r:
                    return r.status

            assert post({"retain_days": 30}) == 200, "合法 retain_days POST 未 200"
            cfg_txt = (d / ".skein/config.yaml").read_text()
            assert "retain_days: 30" in cfg_txt, "POST retain_days 未落盘 config.yaml"
            # 非法: 类型不合的 retain_days 被兜底为默认值 (7), 不污染为非法值
            assert post({"retain_days": "not-a-number"}) == 200, "类型不合 POST 仍应 200 (兜底默认值)"
            assert "retain_days: 7" in (d / ".skein/config.yaml").read_text(), "非法 retain_days 未兜底为默认值"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def main():
    test_prd_and_efficiency()
    test_serve_http()
    print("skein.py 看板测试全过 (prd-checklist / 零无谓写效率不变量 / serve-http: 实时渲染·资产直出·穿越守卫·配置持久化)")


if __name__ == "__main__":
    main()
