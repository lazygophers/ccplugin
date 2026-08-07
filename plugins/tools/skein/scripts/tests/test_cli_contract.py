"""CLI 契约可发现性回归 — 全部用例都来自一次真实 cron 会话里 17 次白跑的 skein 调用。

接缝 = CLI 命令边界 (同 test_stage_hooks.py): 跑真实 skein.py 子进程, 断言退出码 + 回显,
不碰内部实现。覆盖:
1. estimate 带单位后缀 (`30m` / `1.5h`) 被接受, 裸数字仍按小时
2. confirm 一次报全部未就绪项 (收集式), 不是 fail-fast 一条一条挤
3. design.md 测试接缝段有 CLI 写入口 (此前只有校验没有写入)
4. claim 回显带 next[] 派发提示 (缺它就退化成轮询 skein list 干等)
5. `skein task list` / `--status all` 这两个自然猜测不再是错
6. --unattended 需 config 预先授权; 授权后 confirmed_by 留痕
7. --like 克隆既有 task 的 planning 骨架 (周期任务免重复 planning)
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli


def _mk(cli: SkeinCli, ws: Path, tid: str = "demo", **kw: str) -> None:
    args = ["task", "create", tid, "--name", "演示", "--desc", "契约回归"]
    for k, v in kw.items():
        args += [f"--{k}", v]
    cli(ws, *args)


def _fill_planning(cli: SkeinCli, ws: Path, tid: str) -> None:
    """把 tid 填到 confirm 全绿 (prd 六段 + seam + subtask + estimate)。"""
    for type_, text in (("goal", "目标一"), ("scope", "边界一"),
                        ("stories", "As a dev, I want X, so that Y"),
                        ("acceptance", "验收一"), ("verification", "跑命令"),
                        ("testing", "只测外部行为")):
        cli(ws, "prd", "write", tid, "--type", type_, "--list", text)
    cli(ws, "design", "seam", tid, "--list", "走 CLI 边界")
    cli(ws, "subtask", "add", tid, "st1", "--name", "干活", "--desc", "描述", "--estimate", "1")
    cli(ws, "task", "estimate", tid, "--set", "2")


# ---------- 1. estimate 单位 ----------
def test_estimate_accepts_unit_suffix(skein_cli: SkeinCli, ws: Path) -> None:
    """`30m` → 0.5h, `1.5h` → 1.5h, 裸 `2` → 2h。三个 estimate 入口共用同一解析。"""
    _mk(skein_cli, ws, "demo", estimate="30m")
    out = json.loads(skein_cli(ws, "task", "estimate", "demo").stdout)
    assert out["estimate"] == 0.5, f"30m 应解析成 0.5h: {out}"

    skein_cli(ws, "subtask", "add", "demo", "st1",
              "--name", "a", "--desc", "b", "--estimate", "1.5h")
    sub = json.loads(skein_cli(ws, "subtask", "list", "demo").stdout)
    assert any(s["estimate"] == 1.5 for s in sub["subtasks"]), f"1.5h 应解析成 1.5: {sub}"

    skein_cli(ws, "task", "estimate", "demo", "--set", "2")
    assert json.loads(skein_cli(ws, "task", "estimate", "demo").stdout)["estimate"] == 2.0


def test_estimate_error_states_the_unit(skein_cli: SkeinCli, ws: Path) -> None:
    """非法工时的报错必须说清单位 —— 光说 'not a valid float' 换来的只是又一次瞎猜。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "task", "estimate", "demo", "--set", "abc", check=False)
    assert r.returncode != 0
    assert "小时" in r.stdout + r.stderr, f"报错须点明单位: {r.stdout}{r.stderr}"


# ---------- 2. confirm 收集式 ----------
def test_confirm_reports_all_gaps_at_once(skein_cli: SkeinCli, ws: Path) -> None:
    """裸 create 的 task 同时缺 subtask / prd / seam / estimate → 一次全报, 不是只报第一条。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "task", "confirm", "demo", "--summary", check=False)
    assert r.returncode != 0
    msg = r.stdout + r.stderr
    for want in ("subtask", "prd", "接缝", "工时"):
        assert want in msg, f"未就绪清单漏了「{want}」: {msg}"


# ---------- 3. design seam 写入口 ----------
def test_design_seam_has_write_path(skein_cli: SkeinCli, ws: Path) -> None:
    """confirm 拿 seam 当硬门, 就必须有对应的 CLI 写入口 (否则只能 Read+Edit 手改文件)。"""
    _mk(skein_cli, ws)
    skein_cli(ws, "design", "seam", "demo", "--list", "接缝甲\\n接缝乙")
    body = json.loads(skein_cli(ws, "design", "read", "demo").stdout)["body"]
    assert "- 接缝甲" in body and "- 接缝乙" in body, f"seam 未写入: {body}"
    assert "TODO" not in body, f"占位应被整段替换: {body}"


# ---------- 4. claim 派发提示 ----------
def test_claim_returns_dispatch_hints(skein_cli: SkeinCli, ws: Path) -> None:
    """claim 只改状态, 推进靠 main 派 agent → 回显必须点名派谁, 否则调用方只会轮询干等。"""
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    skein_cli(ws, "task", "confirm", "demo", "--approved")

    exec_next = json.loads(skein_cli(ws, "claim").stdout)["exec"]["next"]
    assert exec_next and exec_next[0]["agent"] == "skein:skein-executor", exec_next
    assert exec_next[0]["sid"] == "st1", exec_next

    skein_cli(ws, "subtask", "done", "demo", "st1", "--passed", "ok")
    check_next = json.loads(skein_cli(ws, "claim").stdout)["check"]["next"]
    assert check_next and check_next[0]["agent"] == "skein:skein-checker", check_next
    assert check_next[0]["tid"] == "demo", check_next


# ---------- 5. 自然猜测的命令形态 ----------
def test_task_list_alias_and_status_all(skein_cli: SkeinCli, ws: Path) -> None:
    """`skein task list` (task 组里其余全是 task 子命令) 与 `--status all` 都该直接可用。"""
    _mk(skein_cli, ws)
    via_task = json.loads(skein_cli(ws, "task", "list", "--status", "all", "--json").stdout)
    via_top = json.loads(skein_cli(ws, "list", "--status", "all", "--json").stdout)
    assert via_task == via_top, "task list 应与顶层 list 等价"
    assert [t["id"] for t in via_task["tasks"]] == ["demo"]


# ---------- 6. 无人值守放行 ----------
def test_unattended_requires_config_grant(skein_cli: SkeinCli, ws: Path) -> None:
    """--unattended 未授权即拒 —— 没这道锁, 这个 flag 等于把人审门整个删掉。"""
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    r = skein_cli(ws, "task", "confirm", "demo", "--unattended", check=False)
    assert r.returncode != 0
    assert "confirm.unattended" in r.stdout + r.stderr, f"须指出授权方式: {r.stdout}{r.stderr}"


def test_unattended_after_grant_records_channel(skein_cli: SkeinCli, ws: Path) -> None:
    """授权后放行, 且 confirmed_by 记 'unattended' 而非 'user' —— 无人值守要可审计。"""
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    skein_cli(ws, "config", "set", "confirm.unattended", "true")
    skein_cli(ws, "task", "confirm", "demo", "--unattended")
    t = json.loads((ws / ".skein" / "task" / "demo" / "task.json").read_text(encoding="utf-8"))
    assert t["confirmed_by"] == "unattended", t
    assert t["status"] == "active", t


# ---------- 7. --like 克隆 planning ----------
def test_like_clones_planning_skeleton(skein_cli: SkeinCli, ws: Path) -> None:
    """周期任务第二轮用 --like 克隆上一轮骨架 → 直接过 confirm 门, 不必重写六段 PRD。"""
    _mk(skein_cli, ws, "round1")
    _fill_planning(skein_cli, ws, "round1")

    out = json.loads(skein_cli(ws, "task", "create", "round2", "--name", "第二轮",
                               "--desc", "复用", "--like", "round1").stdout)
    assert out["cloned_from"] == "round1", out
    # planning 门全过 = --summary 能成功返回摘要而非未就绪清单
    summary = json.loads(skein_cli(ws, "task", "confirm", "round2", "--summary").stdout)
    assert "summary" in summary, summary
    # subtask 骨架带过来但执行期字段全部重置 (读 task.json —— subtask list 不回显 started)
    subs = json.loads((ws / ".skein" / "task" / "round2" / "task.json")
                      .read_text(encoding="utf-8"))["subtasks"]
    assert [s["sid"] for s in subs] == ["st1"], subs
    assert subs[0]["status"] == "pending" and subs[0]["started"] is None, subs
    assert subs[0]["estimate"] == 1.0, subs
