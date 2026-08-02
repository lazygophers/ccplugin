#!/usr/bin/env python3
"""skein.py 冒烟测试 — 临时 git 仓跑 init→create→confirm→finish 全链。

无框架, 纯 assert。跑: python3 test_skein.py
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

from conftest import (SKEIN, make_git_repo, make_ws,  # 单一实现, 见 conftest 顶部说明
                      run_git as git, run_skein as sk)
from skeinlib.commands import Skein, _workspace_lock
from skeinlib.config import Config
from skeinlib.task.dag import _sub_pct, _task_pct
from skeinlib.errors import SkeinError
from skeinlib.task.model import (SubtaskStatus, TaskStatus)
from skeinlib.views import _view_board_data


def _load(mod_name: str) -> ModuleType:
    """从 SKEIN 路径动态加载模块并执行。"""
    spec = importlib.util.spec_from_file_location(mod_name, SKEIN)
    assert spec is not None
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        d: Path = Path(td)
        make_git_repo(d)

        # init
        sk(d, "init")
        assert (d / ".skein" / "config.yaml").exists(), "config 缺失"
        # PyYAML 往返: 类型 (int/bool/str) + # 注释
        rt = Config.yaml_load(Config.yaml_dump(
            {"pools": {"work": 2}, "auto_commit": True, "worktree": {"root": ".worktrees"}}))
        assert rt == {"pools": {"work": 2}, "auto_commit": True, "worktree": {"root": ".worktrees"}}, rt
        assert Config.yaml_load("max_active: 2  # 注释\nfoo: bar")["max_active"] == 2, "注释未剥离"
        assert (d / ".skein" / "task.md").exists(), "看板缺失"
        # .gitignore: .skein/ 忽略 task.md, 根 .gitignore 补 worktree_root
        assert "task.md" in (d / ".skein" / ".gitignore").read_text(), ".skein/.gitignore 未忽略 task.md"
        assert ".worktrees/" in (d / ".gitignore").read_text(), "根 .gitignore 未补 worktree_root"
        sk(d, "init")  # 幂等: 二次 init 不重复追加根 .gitignore
        assert (d / ".gitignore").read_text().count(".worktrees/") == 1, "worktree 忽略重复追加"
        # retain_days=0 → finish 即归档 (测归档链路; 默认 7 天惰性归档不便冒烟)
        cfg = d / ".skein/config.yaml"
        cfg.write_text(cfg.read_text().replace("retain_days: 7", "retain_days: 0"))

        def rdy(tid: str) -> None:
            """填实 prd + confirm (吸收 start: 待处理→进行中, 直接建 worktree)。"""
            (d / ".skein/task" / tid / "prd.md").write_text(
                f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
                "## User Stories\n1. As a user, I want X\n\n"
                "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest, 全绿即 pass\n\n## Testing Decisions\n- 复用现有单测\n\n## 索引\n- design.md\n")
            # 填实测试接缝段 (confirm 硬门): scaffold 落的是占位, 不填会被 _validate_seam 挡在工时门之前
            design = d / ".skein/task" / tid / "design.md"
            design.write_text(re.sub(
                r"- \[ \] TODO: 填测试接缝", "- [x] 复用 `test_x.py::test_y` 现有单测", design.read_text()))
            # 工时门: prd 填实但没预计工时 → confirm 拒
            r = sk(d, "confirm", tid, check=False)
            assert r.returncode != 0 and "预计工时" in r.stderr, f"缺 estimate 未拒: {r.stderr}"
            sk(d, "estimate", tid, "--set", "4")
            sk(d, "confirm", tid)

        # create: id 必填且为可读 slug
        out = sk(d, "create", "task-1", "--name", "第一个任务", "--desc", "测试").stdout.strip()
        tid = out.split("\t")[0]
        assert tid == "task-1", f"预期 task-1 得 {tid}"
        t = json.loads((d / ".skein/task/task-1/task.json").read_text())
        assert t["name"] == "第一个任务", t["name"]
        assert t["status"] == "待处理", t["status"]
        # 非法 id (非 slug) + 重复 id 均拒
        assert sk(d, "create", "订单接口", "--name", "x", "--desc", "y", check=False).returncode != 0, "非 slug id 应拒"
        assert sk(d, "create", "task-1", "--name", "x", "--desc", "y", check=False).returncode != 0, "重复 id 应拒"
        assert t["contracts"] == [], "create 未初始化 contracts"
        assert isinstance(t["created"], int), "created 须为时间戳"

        # contract: --add 落盘 + 无参列出
        sk(d, "contract", "task-1", "--add", "输出必须幂等")
        t = json.loads((d / ".skein/task/task-1/task.json").read_text())
        assert t["contracts"] == ["输出必须幂等"], t["contracts"]
        assert "输出必须幂等" in sk(d, "contract", "task-1").stdout, "contract 未列出"

        # start 前须登记 ≥1 subtask (planning 拆分产物)
        sk(d, "subtask", "add", "task-1", "s1", "--name", "核心逻辑", "--desc", "描述", "--estimate", "1")
        s1 = json.loads((d / ".skein/task/task-1/task.json").read_text())["subtasks"][0]
        assert "agent" not in s1, f"subtask 不应再有 agent 字段: {s1}"

        # subtask show: 存在 sid → 0 且含 name; 不存在 sid → 非 0 退出
        r_show = sk(d, "subtask", "show", "task-1", "s1")
        assert r_show.returncode == 0 and "核心逻辑" in r_show.stdout, f"subtask show 未含 name: {r_show.stdout!r}"
        r_show_bad = sk(d, "subtask", "show", "task-1", "nosuch", check=False)
        assert r_show_bad.returncode != 0, "subtask show 不存在 sid 应非 0 退出"

        # confirm task-1 (吸收 start) → worktree 建出
        rdy("task-1")
        t = json.loads((d / ".skein/task/task-1/task.json").read_text())
        assert t["status"] == "进行中", t["status"]
        assert isinstance(t["started"], int), "start 未记 started 时间戳"
        assert not t["worktree"].startswith("/"), f"worktree 须相对: {t['worktree']}"
        wt = d / t["worktree"]  # 相对 project root → 拼绝对
        assert wt.exists(), "worktree 未建"
        top = json.loads((d / ".skein/task.json").read_text())
        assert "focus" not in top, "顶层不应再有 focus 字段"
        # 顶层 task.json 汇总全表: id/状态/deps/worktree
        row1 = next(x for x in top["tasks"] if x["id"] == "task-1")
        assert row1["status"] == "进行中" and row1["worktree"] == t["worktree"], row1

        # session-context: 有 active task → JSON envelope 含 task id
        r = sk(d, "session-context")
        assert r.returncode == 0 and "task-1" in r.stdout, "session-context 未含 active task"
        payload = json.loads(r.stdout)
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart", "注入格式错"
        # git 仓无 .skein/ → 注入 setup 建议 (无 .skein 即 nudge)
        with tempfile.TemporaryDirectory() as bare:
            git(Path(bare), "init", "-q")
            r2 = sk(Path(bare), "session-context")
            assert r2.returncode == 0 and "setup" in r2.stdout, f"无 .skein 应 nudge setup: {r2.stdout!r}"
            assert json.loads(r2.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"

        # task 级并发上限已取消 (design item #6): 多 task 可同时 confirm→进行中, 无需腾位
        sk(d, "create", "task-2", "--name", "第二个", "--desc", "描述")
        sk(d, "subtask", "add", "task-2", "s1", "--name", "x", "--desc", "描述", "--estimate", "1")
        rdy("task-2")
        sk(d, "create", "task-3", "--name", "第三个", "--desc", "描述")
        sk(d, "subtask", "add", "task-3", "s1", "--name", "x", "--desc", "描述", "--estimate", "1")

        # 在 worktree 改文件 → check→finishing→finish 合并回主
        (wt / "feature.txt").write_text("done\n")
        sk(d, "check", "task-1")
        sk(d, "finishing", "task-1")
        sk(d, "finish", "task-1")
        assert (d / "feature.txt").exists(), "finish 未合并回主工作区"
        assert list((d / ".skein/task/archive").glob("*/*/task-1")), "未归档 (日期分层)"
        assert not (d / ".skein/task/task-1").exists(), "归档后 task 残留"
        assert not wt.exists(), "worktree 未销"
        # 归档后顶层 tasks 索引去掉 task-1
        top = json.loads((d / ".skein/task.json").read_text())
        assert not any(x["id"] == "task-1" for x in top["tasks"]), "归档 task 仍留在顶层索引"
        assert any(x["id"] == "task-2" for x in top["tasks"]), "task-2 应仍在顶层索引"

        # deps: task-3 依赖 task-2, task-2 未 finish 前 confirm task-3 应被 deps 门拒
        (d / ".skein/task/task-3/task.json").write_text(
            json.dumps({**json.loads((d / ".skein/task/task-3/task.json").read_text()),
                        "deps": ["task-2"]}, ensure_ascii=False))
        (d / ".skein/task/task-3/prd.md").write_text(
            "# task-3 — PRD\n\n## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
            "## 验收标准\n- 用例通过\n\n## 索引\n- design.md\n")
        design3 = d / ".skein/task/task-3/design.md"
        design3.write_text(re.sub(
            r"- \[ \] TODO: 填测试接缝", "- [x] 复用 `test_x.py::test_y` 现有单测", design3.read_text()))
        sk(d, "estimate", "task-3", "--set", "4")
        r = sk(d, "confirm", "task-3", check=False)
        assert r.returncode != 0 and "前置未完成" in r.stderr, "deps 门未生效"

        # board 渲染无 focus 标记, 列出 active task 行
        board = (d / ".skein/task.md").read_text()
        assert "task-2" in board, "看板缺 task 行"
        assert "focus:" not in board, "看板不应再有 focus footer"

        # archive in_progress task → 销 worktree/branch + 从顶层索引移除
        wt2 = d / json.loads((d / ".skein/task/task-2/task.json").read_text())["worktree"]
        assert wt2.exists()
        sk(d, "archive", "task-2")
        assert not wt2.exists(), "archive 未销 worktree"
        br = subprocess.run(["git", "branch", "--list", "skein/task-2"], cwd=d,
                            capture_output=True, text=True).stdout
        assert "skein/task-2" not in br, "archive 未删 branch"
        top = json.loads((d / ".skein/task.json").read_text())
        assert not any(x["id"] == "task-2" for x in top["tasks"]), "archive 未从顶层索引移除"
        assert sk(d, "current", check=False).returncode == 0, "archive 后 current 崩溃"

        # task 级 ready: task-3 前置(task-2)已归档→视完成 → task-3 可 confirm
        rout = sk(d, "ready").stdout
        assert "task-3" in rout and "可 confirm task" in rout, f"ready 未列可 confirm 的 task-3: {rout!r}"

        # 多 active 并行: task-3 (dep task-2 已归档→视完成) 与 task-4 可同时 active
        sk(d, "confirm", "task-3")
        sk(d, "create", "task-4", "--name", "第四个", "--desc", "描述")
        sk(d, "subtask", "add", "task-4", "s1", "--name", "x", "--desc", "描述", "--estimate", "1")
        rdy("task-4")
        top = json.loads((d / ".skein/task.json").read_text())
        act = {x["id"] for x in top["tasks"] if x["status"] == "进行中"}
        assert act == {"task-3", "task-4"}, f"多 active 并行失效: {act}"
        sk(d, "check", "task-3")
        sk(d, "finishing", "task-3")
        sk(d, "finish", "task-3")
        top = json.loads((d / ".skein/task.json").read_text())
        assert any(x["id"] == "task-4" and x["status"] == "进行中" for x in top["tasks"]), "finish 误伤无关 active"

        # ---- subtask DAG 调度 ----
        sk(d, "create", "task-5", "--name", "编排任务", "--desc", "描述")
        sk(d, "subtask", "add", "task-5", "s1", "--name", "x", "--desc", "描述", "--estimate", "1")
        sk(d, "subtask", "add", "task-5", "s2", "--name", "y", "--desc", "描述", "--estimate", "1")
        sk(d, "subtask", "add", "task-5", "s3", "--deps", "s1,s2", "--name", "z", "--desc", "描述", "--estimate", "1")
        rdy("task-5")  # confirm 直接进行中 (confirm 吸收 start, 无中间态)
        assert (d / ".skein/task/task-5/task.md").exists(), "per-task 看板缺失"
        rdy_out = sk(d, "subtask", "ready", "task-5").stdout
        assert "s1" in rdy_out and "s2" in rdy_out and "s3" not in rdy_out, "就绪批错 (s3 应被依赖挡)"
        # ready 只读: 不改状态
        subs0 = json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"]
        assert all(s["status"] == "待处理" for s in subs0), "ready 误改状态 (应只读)"
        # claim 一次性认领整个就绪批 → s1/s2 标 running
        rout = sk(d, "subtask", "claim", "task-5").stdout
        assert "s1" in rout and "s2" in rout, "claim 未返回就绪批"
        subs_c = json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"]
        st = {s["sid"]: s["status"] for s in subs_c}
        assert st["s1"] == "运行中" and st["s2"] == "运行中", "claim 未标 running"
        # 时间戳: add→created, claim→started, done→finished
        s1 = next(s for s in subs_c if s["sid"] == "s1")
        assert isinstance(s1["created"], int) and isinstance(s1["started"], int), "subtask created/started 未记"
        assert s1["finished"] is None, "未 done 不应有 finished"
        # 满槽 (max_active=2) → start 第三个应报错
        assert sk(d, "subtask", "start", "task-5", "s3", check=False).returncode != 0, "满槽未挡"
        assert "无就绪" in sk(d, "subtask", "claim", "task-5").stdout, "满槽 claim 未阻塞"
        sk(d, "subtask", "done", "task-5", "s1")
        sk(d, "subtask", "done", "task-5", "s2")
        s1d = next(s for s in json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"] if s["sid"] == "s1")
        assert isinstance(s1d["finished"], int), "done 未记 finished 时间戳"
        assert "s3" in sk(d, "subtask", "ready", "task-5").stdout, "依赖全 done 后 s3 未就绪"
        # ready 只读: s3 就绪但未认领仍待处理
        subs = json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"]
        assert {s["sid"]: s["status"] for s in subs}["s3"] == "待处理"
        # ---- claim --dry-run: 只读预览全局就绪批 (旧 pop 折叠进此) ----
        # task-4 仍 active 且 s1 就绪 → s1 出现在全局就绪批预览 (task-4/s1)
        rp = sk(d, "claim", "exec", "--dry-run").stdout
        assert "task-4" in rp and "s1" in rp, f"claim --dry-run 未含 active task 就绪 subtask: {rp!r}"
        rp_all = sk(d, "claim", "--dry-run").stdout
        assert "task-4" in rp_all and "s1" in rp_all and "check/finishing" in rp_all, \
            f"claim --dry-run 未同时返回 exec/check 预览: {rp_all!r}"
        # claim --dry-run 只读: 不改状态
        s4 = json.loads((d / ".skein/task/task-4/task.json").read_text())["subtasks"]
        assert {s["sid"]: s["status"] for s in s4}["s1"] == "待处理", "claim --dry-run 误改状态 (应只读)"
        # task-4 done 掉 s1 后走 check→finishing→finish 收尾; 所有 confirm 过的 task 都已 active,
        # 无「就绪待启动」中间态可提示 (confirm 已吸收 start), 故此处只验 dry-run 不因收尾崩溃
        sk(d, "subtask", "claim", "task-4"); sk(d, "subtask", "done", "task-4", "s1")
        sk(d, "check", "task-4"); sk(d, "finishing", "task-4"); sk(d, "finish", "task-4")
        assert sk(d, "claim", "exec", "--dry-run").returncode == 0, "claim --dry-run 崩溃"
        # ---- DAG 节点框: 长 name/desc 不截断 + 限宽 [208,272] + 多行换行 (高随行数增长, 不加宽避横滚) ----
        longnm = "改造dag_html节点宽自适应不截断完整展示信息"
        sk(d, "subtask", "add", "task-5", "s4", "--name", longnm,
           "--desc", "估文本像素宽全框统一取最大列对齐保底208像素", "--estimate", "1")
        sk(d, "board")  # task.md 落盘 (task.html 演进为 serve 实时渲染, 不再 persist)
        import os
        cwd0 = os.getcwd(); os.chdir(d)
        try:
            sk_obj = Skein()
            data = _view_board_data(sk_obj._snapshot())
        finally:
            os.chdir(cwd0)
        # DAG 全由前端从 cards[].subNodes 推 (节点 = [id,name,status,deps,pct,desc]);
        # 后端只出结构化数据, 验长 name/desc 完整不截断 (核心诉求: 不丢信息)
        card5 = next(c for c in data["cards"] if c["id"] == "task-5")
        s4node = next((n for n in card5["subNodes"] if n[0] == "s4"), None)
        assert s4node is not None, "cards[task-5].subNodes 缺 s4 节点"
        assert s4node[1] == longnm, f"长 name 被截断/丢失: {s4node[1]!r}"
        assert "估文本像素宽全框统一取最大列对齐保底208像素" in s4node[5], f"长 desc 被截断: {s4node[5]!r}"

    test_setup()
    test_lock()
    test_multirepo()
    test_deps_ordering()
    test_progress_pct()
    test_seam_gate()
    test_prd_section_gate()
    print("skein.py 冒烟测试全过 (init/create/confirm/check/finishing/finish/deps门/看板/archive清理/多active并行/subtask-DAG/setup迁移/多子git worktree)")


def test_progress_pct() -> None:
    # 进度 = 状态区间 + subtask 完成度均值线性插值; 覆盖 pending/research/active/check/done × 有无 subtask

    def sub(status: str, crit: int = 0, done: int = 0) -> dict[str, Any]:
        return {"status": status, "acceptance": [f"c{i}" for i in range(crit)],
                "acceptance_done": [f"c{i}" for i in range(done)]}

    def pct(status: str, subs: list[dict[str, Any]] | None = None) -> int:
        return _task_pct({"status": status, "subtasks": subs or []})

    # 无 subtask: 取状态区间中点
    assert pct(TaskStatus.PENDING) == 2, pct(TaskStatus.PENDING)      # (0,5)
    assert pct(TaskStatus.RESEARCH) == 7, pct(TaskStatus.RESEARCH)    # (5,10)
    assert pct(TaskStatus.ACTIVE) == 47, pct(TaskStatus.ACTIVE)       # (10,85)
    assert pct(TaskStatus.CHECK) == 90, pct(TaskStatus.CHECK)         # (85,95)
    assert pct(TaskStatus.DONE) == 100, pct(TaskStatus.DONE)
    # 有 subtask: 在状态区间内按 subtask 完成度均值线性插值
    allpend = [sub(SubtaskStatus.PENDING) for _ in range(3)]     # 每个 _sub_pct=2 → 均值 2
    assert pct(TaskStatus.ACTIVE, allpend) == 11, pct(TaskStatus.ACTIVE, allpend)    # 10+75*.02
    assert pct(TaskStatus.PENDING, allpend) == 0, pct(TaskStatus.PENDING, allpend)   # 0+5*.02
    assert pct(TaskStatus.RESEARCH, allpend) == 5, pct(TaskStatus.RESEARCH, allpend) # 5+5*.02
    assert pct(TaskStatus.CHECK, allpend) == 85, pct(TaskStatus.CHECK, allpend)      # 85+10*.02
    mixed = [sub(SubtaskStatus.DONE), sub(SubtaskStatus.DONE), sub(SubtaskStatus.PENDING)]        # 均值 (100+100+2)/3
    assert pct(TaskStatus.ACTIVE, mixed) == 60, pct(TaskStatus.ACTIVE, mixed)
    # subtask 全完成也不给满 — 未走完状态机不封顶到 100
    alldone = [sub(SubtaskStatus.DONE) for _ in range(3)]
    assert pct(TaskStatus.ACTIVE, alldone) == 85, pct(TaskStatus.ACTIVE, alldone)    # 区间上界
    assert pct(TaskStatus.CHECK, alldone) == 95, pct(TaskStatus.CHECK, alldone)      # 未验收不给 100
    assert pct(TaskStatus.DONE, allpend) == 100, "done 强制 100"
    # 验收项粒度: 在 subtask 状态区间内按 验收done/验收 插值, 无验收项取中点
    assert _sub_pct(sub(SubtaskStatus.RUNNING, crit=4, done=1)) == 30         # 10+80*.25
    assert _sub_pct(sub(SubtaskStatus.RUNNING)) == 50                         # (10,90) 中点
    assert _sub_pct(sub(SubtaskStatus.PENDING)) == 2                          # (0,5) 中点
    assert _sub_pct(sub(SubtaskStatus.FAILED)) == 50, "失败与运行同区间, 重试不回跳"
    assert _sub_pct(sub(SubtaskStatus.DONE, crit=4, done=1)) == 100, "done 强制 100"


def test_deps_ordering() -> None:
    # deps 命令 (dedup 补序织 DAG): pending+空deps 可写; 已有 deps/自引用/不存在/成环 全拒
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        make_git_repo(d)
        sk(d, "init")
        sk(d, "create", "schema-x", "--name", "s", "--desc", "d")
        sk(d, "create", "api-x", "--name", "a", "--desc", "d")
        sk(d, "create", "ui-x", "--name", "u", "--desc", "d", "--deps", "api-x")
        # 正常补: api 无 deps → 依赖 schema, 可读回
        sk(d, "deps", "api-x", "--set", "schema-x")
        assert "schema-x" in sk(d, "deps", "api-x").stdout, "补序未写入"
        # 已有 deps 的 task 不可改
        r = sk(d, "deps", "ui-x", "--set", "schema-x", check=False)
        assert r.returncode != 0 and "既有依赖不可改" in r.stderr, "已有 deps 未拒"
        # 自引用拒
        r = sk(d, "deps", "schema-x", "--set", "schema-x", check=False)
        assert r.returncode != 0 and "自引用" in r.stderr, "自引用未拒"
        # 不存在前置拒
        r = sk(d, "deps", "schema-x", "--set", "nope", check=False)
        assert r.returncode != 0 and "不存在" in r.stderr, "不存在前置未拒"
        # 成环拒 (schema→ui→api→schema)
        r = sk(d, "deps", "schema-x", "--set", "ui-x", check=False)
        assert r.returncode != 0 and "成环" in r.stderr, "成环未拒"
        sk(d, "doctor")  # 无违规


def test_lock() -> None:
    # 写锁: 持锁时另一获取者应阻塞到超时 → SkeinError (库侧不再抛 SystemExit, 见 skeinlib/errors.py)
    with tempfile.TemporaryDirectory() as d:
        lp = Path(d) / ".lock"
        with _workspace_lock(lp, timeout=1.0):
            try:
                with _workspace_lock(lp, timeout=0.2):
                    raise AssertionError("持锁时不应拿到第二把锁")
            except SkeinError:
                pass  # 预期: 超时抛领域异常, 进程内就能断言 (从前只能起子进程看退出码)
        # 释放后可重新获取
        with _workspace_lock(lp, timeout=0.2):
            pass


def test_multirepo() -> None:
    # 多子 git: 非 git 父目录下两并列 repo, task 声明 --repos → start 各建 worktree, finish 各自合入
    with tempfile.TemporaryDirectory() as td:
        d: Path = Path(td)
        for r in ("repoA", "repoB"):
            sub = d / r
            sub.mkdir()
            git(sub, "init", "-q")
            git(sub, "config", "user.email", "t@t.dev")
            git(sub, "config", "user.name", "t")
            (sub / "f.txt").write_text(f"base-{r}\n")
            git(sub, "add", "-A"); git(sub, "commit", "-qm", "init")
        sk(d, "init")
        sk(d, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
        sk(d, "create", "feat", "--name", "跨仓", "--desc", "改两仓", "--repos", "repoA,repoB")
        rl = sk(d, "repos", "feat").stdout
        assert "repoA" in rl and "repoB" in rl, rl
        sk(d, "subtask", "add", "feat", "s1", "--name", "改A", "--desc", "d", "--estimate", "1")
        (d / ".skein/task/feat/prd.md").write_text(
            "# feat — PRD\n\n## 目标\n- 改两仓\n\n## 边界\n- 范围内: a\n\n"
            "## User Stories\n1. As a user, I want cross-repo changes\n\n"
            "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest, 全绿即 pass\n\n## Testing Decisions\n- 复用现有单测\n\n## 索引\n- design.md\n")
        design = d / ".skein/task/feat/design.md"
        design.write_text(re.sub(
            r"- \[ \] TODO: 填测试接缝", "- [x] 复用 `test_x.py::test_y` 现有单测", design.read_text()))
        sk(d, "estimate", "feat", "--set", "4")
        sk(d, "confirm", "feat")  # 待处理→进行中 (confirm 吸收 start): 用户确认门 + 建 worktree
        # worktree 落各子仓内部 (<repo>/.worktrees/skein-<id>), 非旧版根级 .worktrees/skein-<id>/<repo>
        wa = d / "repoA/.worktrees/skein-feat"
        wb = d / "repoB/.worktrees/skein-feat"
        assert wa.is_dir() and wb.is_dir(), "多子 git worktree 未建全"
        # 各 worktree 内改文件并提交前留给 finish 提交
        (wa / "f.txt").write_text("base-repoA\nchangeA\n")
        (wb / "f.txt").write_text("base-repoB\nchangeB\n")
        sk(d, "check", "feat")
        sk(d, "finishing", "feat")
        sk(d, "finish", "feat")
        assert "changeA" in (d / "repoA/f.txt").read_text(), "repoA 未合入"
        assert "changeB" in (d / "repoB/f.txt").read_text(), "repoB 未合入"
        # worktree 与分支清理
        assert not wa.exists() and not wb.exists(), "worktree 未销"
        for r in ("repoA", "repoB"):
            br = subprocess.run(["git", "branch", "--list", "skein/feat"], cwd=d / r,
                                capture_output=True, text=True).stdout
            assert "skein/feat" not in br, f"{r} 分支未删"


def test_seam_gate() -> None:
    """confirm 的测试接缝门: 占位未填 / 缺段硬拒; 填实才放行。"""
    with tempfile.TemporaryDirectory() as td:
        d: Path = Path(td)
        make_ws(d)

        def _prd(tid: str) -> None:
            (d / ".skein/task" / tid / "prd.md").write_text(
                f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
                "## User Stories\n1. As a user, I want X\n\n"
                "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest, 全绿即 pass\n\n## Testing Decisions\n- 复用现有单测\n\n## 索引\n- design.md\n")

        def _ready(tid: str) -> None:
            sk(d, "create", tid, "--name", tid, "--desc", "d")
            sk(d, "subtask", "add", tid, "s1", "--name", "n", "--desc", "d", "--estimate", "1")
            _prd(tid)
            sk(d, "estimate", tid, "--set", "4")

        _ready("task-one")
        r = sk(d, "confirm", "task-one", check=False)
        assert r.returncode != 0, "测试接缝占位不该放行"
        assert "测试接缝段仍是占位未填" in r.stderr, f"占位未报错: {r.stderr}"

        _ready("task-two")
        design = d / ".skein/task/task-two/design.md"
        design.write_text(re.sub(
            r"- \[ \] TODO: 填测试接缝", "- [x] 复用 `test_x.py::test_y` 现有单测", design.read_text()))
        r = sk(d, "confirm", "task-two", check=False)
        assert r.returncode == 0, f"填实后仍拒: {r.stderr}"
        assert "测试接缝" not in r.stderr, f"填实后仍有接缝错误: {r.stderr}"

        _ready("task-three")
        (d / ".skein/task/task-three/design.md").write_text("# task-three — 详细设计\n\n无接缝段\n")
        r = sk(d, "confirm", "task-three", check=False)
        assert r.returncode != 0, "缺测试接缝段不该放行"
        assert "缺测试接缝段" in r.stderr, f"缺段未报错: {r.stderr}"


def test_prd_section_gate() -> None:
    """confirm 的 prd 章节门 (`validate_prd`): 六段齐备顺序对 → 放行;
    四段/残缺/顺序错 → 硬拒 (非零退出 + 报错含标准章节清单)。
    """
    with tempfile.TemporaryDirectory() as td:
        d: Path = Path(td)
        make_ws(d)

        def _seam_fill(tid: str) -> None:
            design = d / ".skein/task" / tid / "design.md"
            design.write_text(re.sub(
                r"- \[ \] TODO: 填测试接缝", "- [x] 复用 `test_x.py::test_y` 现有单测",
                design.read_text()))

        def _ready(tid: str, prd_body: str) -> None:
            sk(d, "create", tid, "--name", tid, "--desc", "d")
            sk(d, "subtask", "add", tid, "s1", "--name", "n", "--desc", "d", "--estimate", "1")
            (d / ".skein/task" / tid / "prd.md").write_text(prd_body)
            _seam_fill(tid)
            sk(d, "estimate", tid, "--set", "4")

        # 场景 1: 标准六段齐备顺序对 → 放行, 无「旧四段」告警
        _ready("v6-task",
               "# v6-task — PRD\n\n## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
               "## User Stories\n1. As a user, I want X\n\n"
               "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest, 全绿即 pass\n\n## Testing Decisions\n- 复用现有单测\n\n"
               "## 索引\n- design.md\n")
        r = sk(d, "confirm", "v6-task", check=False)
        assert r.returncode == 0, f"标准六段不该被拒: {r.stderr}"
        assert "旧四段" not in r.stderr, f"六段不该报旧四段告警: {r.stderr}"

        # 场景 2: 四段 PRD 已退役 → 硬拒
        _ready("v4-task",
               "# v4-task — PRD\n\n## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
               "## 验收标准\n- 用例通过\n\n## 索引\n- design.md\n")
        r = sk(d, "confirm", "v4-task", check=False)
        assert r.returncode != 0, "四段 PRD 不该放行"
        assert "二级章节须为" in r.stderr, f"四段 PRD 未报标准清单: {r.stderr}"

        # 场景 3: 章节残缺 (缺「边界」) → 硬拒
        sk(d, "create", "bad-task", "--name", "bad-task", "--desc", "d")
        sk(d, "subtask", "add", "bad-task", "s1", "--name", "n", "--desc", "d", "--estimate", "1")
        (d / ".skein/task/bad-task/prd.md").write_text(
            "# bad-task — PRD\n\n## 目标\n- 解决 X\n\n## 验收标准\n- 用例通过\n\n## 索引\n- design.md\n")
        _seam_fill("bad-task")
        sk(d, "estimate", "bad-task", "--set", "4")
        r = sk(d, "confirm", "bad-task", check=False)
        assert r.returncode != 0, "章节残缺 (既非 V4 又非 V6) 不该放行"
        assert "二级章节须为" in r.stderr, f"残缺章节未报标准清单: {r.stderr}"


def test_setup() -> None:
    # 新仓 setup: 无 trellis → 建本地 spec, manifest trellis_present=false
    with tempfile.TemporaryDirectory() as td:
        d: Path = Path(td)
        git(d, "init", "-q")
        m = json.loads(sk(d, "setup").stdout)
        assert m["trellis_present"] is False and m["spec_needs_reorg"] is False, m
        assert (d / ".skein/spec").is_dir() and not (d / ".skein/spec").is_symlink(), "本地 spec 未建"

    def _mk_trellis(d: Path) -> None:
        (d / ".trellis/spec").mkdir(parents=True)
        (d / ".trellis/spec/git.md").write_text("# 禁 force push\n")
        (d / ".trellis/task/x").mkdir(parents=True)
        (d / ".trellis/task/x/task.json").write_text('{"id":"x","title":"任务X","status":"in_progress"}')
        (d / ".trellis/task/x/prd.md").write_text("# PRD\n")  # planning 工件应随迁
        (d / ".trellis/task/archive/2026/01-01/old").mkdir(parents=True)  # 归档不迁
        (d / ".trellis/task/archive/2026/01-01/old/task.json").write_text('{"id":"old"}')
        (d / ".trellis/hooks").mkdir()  # 接线: 无条件删
        (d / ".trellis/settings.json").write_text("{}")
        (d / ".claude/skills/foo-trellis").mkdir(parents=True)
        # 原生 trellis 注入的 canonical hook 脚本 (名字不含 trellis) + 用户自有 rust-fmt (须保留)
        (d / ".claude/hooks").mkdir(parents=True, exist_ok=True)
        for s in ("session-start.py", "guard-version.py", "rust-fmt.py"):
            (d / ".claude/hooks" / s).write_text("print(1)\n")
        (d / ".claude/settings.json").write_text(json.dumps({"hooks": {
            "PreToolUse": [{"matcher": "Edit", "hooks": [{"type": "command", "command": "python3 .claude/hooks/guard-version.py"}]}],
            "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "python3 .claude/hooks/session-start.py"}]}],
            "PostToolUse": [{"matcher": "Edit", "hooks": [{"type": "command", "command": "python3 .claude/hooks/rust-fmt.py"}]}],
        }}))

    def _assert_migrated(d: Path, m: dict[str, Any], mode: str) -> None:
        assert m["mode"] == mode and m["trellis_present"] == (mode == "compat"), m
        assert m["spec_copied"] and m["spec_needs_reorg"], m
        # 独立拷贝 (非软链): trellis 零改动
        assert (d / ".skein/spec").is_dir() and not (d / ".skein/spec").is_symlink(), "spec 应独立拷贝非软链"
        assert (d / ".skein/spec/git.md").exists(), "spec 未拷入 .skein"
        # 物理迁移 task: 翻译 + planning 工件, 归档不迁
        assert any(t["id"] == "x" and t["migrated"] for t in m["trellis_tasks"]), "未迁移 trellis task"
        assert not any(t["id"] == "old" for t in m["trellis_tasks"]), "归档 task 误迁"
        assert (d / ".skein/task/x/task.json").exists() and (d / ".skein/task/x/prd.md").exists(), "task 未物理迁入"
        tj = json.loads((d / ".skein/task/x/task.json").read_text())
        assert tj["name"] == "任务X" and tj["status"] == "pending", ("task.json 未翻译为 skein schema", tj)
        # 接线无条件删 (两模式)
        assert any("hooks" in r for r in m["wiring_removed"]), "trellis 接线未删"
        assert not (d / ".claude/skills/foo-trellis").exists(), ".claude trellis 残留未删"
        # canonical trellis hook 剔除: settings 条目 + 脚本文件都删; rust-fmt (用户自有) 原样保留
        hooks = json.loads((d / ".claude/settings.json").read_text()).get("hooks", {})
        assert "PreToolUse" not in hooks and "SessionStart" not in hooks, ("canonical hook 条目未剔", hooks)
        assert hooks["PostToolUse"][0]["hooks"][0]["command"].endswith("rust-fmt.py"), ("rust-fmt 误删", hooks)
        assert not (d / ".claude/hooks/session-start.py").exists(), "canonical hook 脚本未删"
        assert not (d / ".claude/hooks/guard-version.py").exists(), "canonical hook 脚本未删"
        assert (d / ".claude/hooks/rust-fmt.py").exists(), "用户 rust-fmt.py 误删"
        assert m["settings_need_manual_edit"], "settings 需手工剔除未标记"
        # trellisx 插件在 settings.local.json 禁用 (防双注入)
        assert "trellisx@ccplugin-market" in m["trellisx_disabled"], "trellisx 插件未禁用"
        sl = json.loads((d / ".claude/settings.local.json").read_text())
        assert sl["enabledPlugins"]["trellisx@ccplugin-market"] is False, "settings.local.json 未禁 trellisx"

    # 兼容模式: 拷 spec + 迁 task + 删接线, 留 .trellis 数据
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        git(d, "init", "-q")
        _mk_trellis(d)
        m = json.loads(sk(d, "setup").stdout)
        _assert_migrated(d, m, "compat")
        assert (d / ".trellis/spec/git.md").exists(), "兼容模式误删 .trellis 数据"
        assert not (d / ".trellis/hooks").exists(), "兼容模式未删 trellis 接线"
        assert m["trellis_removed"] is False, m

    # --full 模式: 兼容全套 + 整删 .trellis
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _mk_trellis(d)
        m = json.loads(sk(d, "setup", "--full").stdout)
        _assert_migrated(d, m, "full")
        assert not (d / ".trellis").exists(), "--full 未整删 .trellis"
        assert m["trellis_removed"] is True, m


if __name__ == "__main__":
    main()
