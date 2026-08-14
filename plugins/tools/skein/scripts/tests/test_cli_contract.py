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
8. subtask start 不得在 task 未 confirm 时放行 (否则人审门形同虚设)
9. `task update --status` 这类猜测给出状态机指引
10. prd check 的 --list 是匹配串不是序号 (与 write/add 的 --list 同名反义)
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli, run_git


def _sub(ws: Path, tid: str) -> list[dict[str, object]]:
    t = json.loads((ws / ".skein" / "task" / tid / "task.json").read_text(encoding="utf-8"))
    return list(t["subtasks"])


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

    skein_cli(ws, "subtask", "done", "demo", "st1")
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


# ---------- 8. subtask start 不得绕过 confirm 人审门 ----------
def test_subtask_start_blocked_before_confirm(skein_cli: SkeinCli, ws: Path) -> None:
    """pending task 的 subtask 不能 start —— 否则活全干完了 task 还卡 pending 进不了 check,
    人审门等于没发生 (实测有会话正是这么绕过去的)。"""
    _mk(skein_cli, ws)
    skein_cli(ws, "subtask", "add", "demo", "st1",
              "--name", "a", "--desc", "b", "--estimate", "1")
    r = skein_cli(ws, "subtask", "start", "demo", "st1", check=False)
    assert r.returncode != 0, "pending task 的 subtask 不该能 start"
    assert "confirm" in r.stdout + r.stderr, f"报错须指向 confirm: {r.stdout}{r.stderr}"
    assert _sub(ws, "demo")[0]["status"] == "pending", "被拒后状态不该变"


def test_subtask_start_allowed_after_confirm(skein_cli: SkeinCli, ws: Path) -> None:
    """confirm 过门进 active 后, 同一条 start 正常放行 (证明上面那道门不是一刀切)。"""
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    skein_cli(ws, "task", "confirm", "demo", "--approved")
    skein_cli(ws, "subtask", "start", "demo", "st1")
    assert _sub(ws, "demo")[0]["status"] == "running", _sub(ws, "demo")


def test_research_task_only_starts_research_subtask(skein_cli: SkeinCli, ws: Path) -> None:
    """调研中 task 只放行 phase=research 的 subtask, exec 的仍须先 plan→confirm。"""
    _mk(skein_cli, ws)
    skein_cli(ws, "subtask", "add", "demo", "rs1", "--name", "查", "--desc", "查",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "subtask", "add", "demo", "ex1", "--name", "做", "--desc", "做",
              "--estimate", "1")
    skein_cli(ws, "task", "research", "demo")
    skein_cli(ws, "subtask", "start", "demo", "rs1")  # research 放行
    r = skein_cli(ws, "subtask", "start", "demo", "ex1", check=False)
    assert r.returncode != 0, "调研中不该能 start exec subtask"
    assert "plan" in r.stdout + r.stderr, f"报错须指向 plan: {r.stdout}{r.stderr}"


# ---------- 9. 未知命令的状态机指引 ----------
def test_task_update_guess_gets_state_machine_hint(skein_cli: SkeinCli, ws: Path) -> None:
    """`task update --status X` 是最自然的猜测, 裸 "No such command" 只换来第二次瞎猜。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "task", "update", "demo", "--status", "active", check=False)
    msg = r.stdout + r.stderr
    assert "confirm" in msg and "finish" in msg, f"须列出逐阶段命令: {msg}"


# ---------- 10. prd check 的 --list 是匹配串不是序号 ----------
def test_prd_check_list_help_covers_both_forms(skein_cli: SkeinCli, ws: Path) -> None:
    """write/add 的 --list 是内容, check 的 --list 是匹配串 —— 同名反义, help 必须点破;
    序号形态现已受支持, help 也要写明, 免得调用方还得试一轮才知道。"""
    out = skein_cli(ws, "prd", "check", "--help").stdout
    assert "子串" in out and "第 N 条" in out, f"--list help 须写清两种形态: {out}"


def test_prd_check_by_substring_or_index_works(skein_cli: SkeinCli, ws: Path) -> None:
    """按原文子串勾选生效; 纯数字按第 N 条勾, 越界才报错。"""
    _mk(skein_cli, ws)
    skein_cli(ws, "prd", "write", "demo", "--type", "goal", "--list", "交付完整报告")
    r = skein_cli(ws, "prd", "check", "demo", "--type", "goal", "--list", "9", check=False)
    assert r.returncode != 0 and "越界" in r.stdout + r.stderr, f"越界序号应报错: {r.stdout}"
    skein_cli(ws, "prd", "uncheck", "demo", "--type", "goal", "--list", "1")
    skein_cli(ws, "prd", "check", "demo", "--type", "goal", "--list", "1")
    body1 = json.loads(skein_cli(ws, "prd", "read", "demo", "--type", "goal").stdout)["body"]
    assert "- [x] 交付完整报告" in body1, f"序号勾选未生效: {body1}"
    skein_cli(ws, "prd", "uncheck", "demo", "--type", "goal", "--list", "交付完整报告")
    skein_cli(ws, "prd", "check", "demo", "--type", "goal", "--list", "交付完整报告")
    body = json.loads(skein_cli(ws, "prd", "read", "demo", "--type", "goal").stdout)["body"]
    assert "- [x] 交付完整报告" in body, f"子串勾选未生效: {body}"


# ---------- 11. flow run 调度契约 ----------
def test_flow_run_claims_and_dispatches_without_running_agents(
    skein_cli: SkeinCli, ws: Path,
) -> None:
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    skein_cli(ws, "task", "confirm", "demo", "--approved")

    dry = json.loads(skein_cli(ws, "flow", "run", "--dry-run").stdout)
    assert dry["dry_run"] is True
    assert _sub(ws, "demo")[0]["status"] == "pending"

    result = json.loads(skein_cli(ws, "flow", "run").stdout)["result"]
    assert result["exec"]["next"][0]["agent"] == "skein:skein-executor"
    assert result["exec"]["next"][0]["sid"] == "st1"
    assert _sub(ws, "demo")[0]["status"] == "running"


def test_flow_run_advances_to_check_without_confirm_or_finish(
    skein_cli: SkeinCli, ws: Path,
) -> None:
    _mk(skein_cli, ws)
    _fill_planning(skein_cli, ws, "demo")
    skein_cli(ws, "task", "confirm", "demo", "--approved")
    skein_cli(ws, "subtask", "done", "demo", "st1")

    result = json.loads(skein_cli(ws, "flow", "run").stdout)["result"]
    assert result["check"]["next"][0]["agent"] == "skein:skein-checker"
    status = json.loads(skein_cli(ws, "task", "status", "demo", "--json").stdout)["task"]["status"]
    assert status == "check"


def test_report_state_mismatch_is_reported(skein_cli: SkeinCli, ws: Path) -> None:
    _mk(skein_cli, ws)
    skein_cli(ws, "subtask", "add", "demo", "rs1", "--name", "调研", "--desc", "资料",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "task", "estimate", "demo", "--set", "1")
    skein_cli(ws, "task", "research", "demo")
    report = ws / ".skein" / "task" / "demo" / "research" / "rs1.md"
    report.parent.mkdir()
    report.write_text("# report\n", encoding="utf-8")

    result = json.loads(skein_cli(ws, "flow", "run", "--dry-run").stdout)["result"]
    assert {m["sid"] for m in result["exec"]["mismatches"]} == {"rs1"}
    skein_cli(ws, "subtask", "start", "demo", "rs1")
    result = json.loads(skein_cli(ws, "flow", "run", "--dry-run").stdout)["result"]
    assert {m["sid"] for m in result["exec"]["mismatches"]} == {"rs1"}


def test_multi_repo_requires_repo_and_maps_dispatch_workdirs(
    skein_cli: SkeinCli, ws: Path,
) -> None:
    skein_cli(ws, "config", "set", "worktree.enabled", "true")
    for name in ("child-a", "child-b"):
        child = ws / name
        child.mkdir()
        run_git(child, "init", "-q")
        run_git(child, "config", "user.email", "t@t.dev")
        run_git(child, "config", "user.name", "t")
        (child / "seed.txt").write_text("s\n")
        run_git(child, "add", "-A")
        run_git(child, "commit", "-qm", "seed")

    _mk(skein_cli, ws)
    skein_cli(ws, "task", "repos", "demo", "--set", "child-a,child-b")
    missing = skein_cli(ws, "subtask", "add", "demo", "st1", "--name", "干活",
                        "--desc", "描述", "--estimate", "1", check=False)
    assert missing.returncode != 0 and "--repo" in missing.stdout + missing.stderr
    unknown = skein_cli(ws, "subtask", "add", "demo", "st1", "--name", "干活",
                        "--desc", "描述", "--estimate", "1", "--repo", "other", check=False)
    assert unknown.returncode != 0 and "未声明 repo" in unknown.stdout + unknown.stderr
    for sid, repo in (("st1", "child-a"), ("st2", "child-b")):
        skein_cli(ws, "subtask", "add", "demo", sid, "--name", "干活", "--desc", "描述",
                  "--estimate", "1", "--repo", repo)
    for type_, text in (("goal", "目标一"), ("scope", "边界一"),
                        ("stories", "As a dev, I want X, so that Y"),
                        ("acceptance", "验收一"), ("verification", "跑命令"),
                        ("testing", "只测外部行为")):
        skein_cli(ws, "prd", "write", "demo", "--type", type_, "--list", text)
    skein_cli(ws, "design", "seam", "demo", "--list", "走 CLI 边界")
    skein_cli(ws, "task", "estimate", "demo", "--set", "2")
    skein_cli(ws, "task", "confirm", "demo", "--approved")
    result = json.loads(skein_cli(ws, "flow", "run", "--dry-run").stdout)["result"]
    by_sid = {item["subtask"]: item for item in result["exec"]["ready"]}
    assert by_sid["st1"]["workdir"] == str(ws / "child-a" / ".worktrees" / "skein-demo")
    assert by_sid["st2"]["workdir"] == str(ws / "child-b" / ".worktrees" / "skein-demo")


# ---------- 12. 报错自足 / 常见写法直接收 (session 9facb9db: 12 个回合废在猜参数上) ----------
def test_positional_value_equals_set(skein_cli: SkeinCli, ws: Path) -> None:
    """`--set X` 与位置写法 `<id> X` 等价 —— 五条同构命令 (priority/estimate/repos/deps/parent)
    抽 estimate/deps 各验一条。原先位置写法只报 `Got unexpected extra argument(s)`。"""
    _mk(skein_cli, ws, "demo")
    _mk(skein_cli, ws, "dep-a")
    skein_cli(ws, "task", "estimate", "demo", "15")
    assert json.loads(skein_cli(ws, "task", "estimate", "demo").stdout)["estimate"] == 15.0
    skein_cli(ws, "task", "deps", "demo", "dep-a")
    assert "dep-a" in skein_cli(ws, "task", "deps", "demo").stdout


def test_unknown_option_error_lists_available_options(skein_cli: SkeinCli, ws: Path) -> None:
    """选项名猜错时报错里直接列出这条命令收哪些选项, 不必再跑一次 `--help`。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "task", "deps", "demo", "--add", "dep-a", check=False)
    assert r.returncode != 0
    assert "--set" in r.stdout + r.stderr, f"须列出可用选项: {r.stdout}{r.stderr}"


def test_prd_read_without_type_returns_whole_doc(skein_cli: SkeinCli, ws: Path) -> None:
    """`prd read <id>` 省略 --type = 读全文, 不再报 `Missing option '--type'`。"""
    _mk(skein_cli, ws)
    body = json.loads(skein_cli(ws, "prd", "read", "demo").stdout)["body"]
    assert "## 目标" in body and "## 验收标准" in body, body


def test_prd_write_accepts_paired_type_list(skein_cli: SkeinCli, ws: Path) -> None:
    """`--type`/`--list` 成对重复 = 一回合写多章 (PRD 七段原本七次调用)。"""
    _mk(skein_cli, ws)
    skein_cli(ws, "prd", "write", "demo",
              "--type", "goal", "--list", "目标一",
              "--type", "scope", "--list", "边界一")
    body = json.loads(skein_cli(ws, "prd", "read", "demo").stdout)["body"]
    assert "目标一" in body and "边界一" in body, body
    bad = skein_cli(ws, "prd", "write", "demo", "--type", "goal", "--list", "a",
                    "--type", "scope", check=False)
    assert bad.returncode != 0
    assert "成对" in bad.stdout + bad.stderr, f"不成对须说清收到几个: {bad.stdout}{bad.stderr}"


def test_subtask_missing_sid_error_carries_usage(skein_cli: SkeinCli, ws: Path) -> None:
    """漏 sid 的报错带完整用法行 —— 只说「需要 sid」不说 sid 摆哪, 换来的是再跑一次 --help。"""
    _mk(skein_cli, ws)
    r = skein_cli(ws, "subtask", "add", "demo", "--name", "x", "--desc", "y",
                  "--estimate", "1", check=False)
    assert r.returncode != 0
    assert "subtask add <tid> <sid>" in r.stdout + r.stderr, f"须带用法行: {r.stdout}{r.stderr}"


def test_help_describes_repeatable_prd_types_and_subtask_add_options(
        skein_cli: SkeinCli, ws: Path) -> None:
    prd_help = skein_cli(ws, "prd", "write", "--help").stdout
    assert "可重复传" in prd_help and "一次写多段" in prd_help, prd_help
    subtask_help = skein_cli(ws, "subtask", "--help").stdout
    add_usage = next(line for line in subtask_help.splitlines() if line.strip().startswith("add"))
    assert "--check" in add_usage and "--phase" in add_usage, add_usage


def test_unknown_command_error_lists_available_commands(skein_cli: SkeinCli, ws: Path) -> None:
    r = skein_cli(ws, "unknown", check=False)
    msg = r.stdout + r.stderr
    assert r.returncode != 0
    assert "可用子命令:" in msg and "task" in msg and "subtask" in msg, msg


# ---------- 13. prd write 的覆盖必须可见 + `--list a b c` 收多条 ----------
def test_prd_write_reports_cleared_items(skein_cli: SkeinCli, ws: Path) -> None:
    """write 是整章清重建, 回显须报清掉几条/写进几条 —— 否则逐条 write 会静默丢数据。
    占位 `- [ ] TODO:` 是模板初始态, 不计入 cleared。"""
    _mk(skein_cli, ws)
    first = json.loads(skein_cli(ws, "prd", "write", "demo", "--type", "acceptance",
                                 "--list", "验收一\\n验收二\\n验收三").stdout)
    assert first["written"] == 3, first
    assert first["cleared"] == 0, f"清的是 TODO 占位, 不该报警: {first}"
    second = json.loads(skein_cli(ws, "prd", "write", "demo", "--type", "acceptance",
                                  "--list", "验收四").stdout)
    assert (second["cleared"], second["written"]) == (3, 1), f"须报清掉 3 条只写 1 条: {second}"


def test_prd_write_accepts_bare_positional_items(skein_cli: SkeinCli, ws: Path) -> None:
    """`--list "a" "b" "c"` 不再报 unexpected extra argument, 三条并入同一段一次写完。
    与 --type/--list 成对重复共存: 位置参数只并入最后一个 --list。"""
    _mk(skein_cli, ws)
    out = json.loads(skein_cli(ws, "prd", "write", "demo", "--type", "acceptance",
                               "--list", "验收一", "验收二", "验收三").stdout)
    assert out["written"] == 3, out
    body = json.loads(skein_cli(ws, "prd", "read", "demo", "--type", "acceptance").stdout)["body"]
    assert all(x in body for x in ("验收一", "验收二", "验收三")), body

    skein_cli(ws, "prd", "write", "demo",
              "--type", "goal", "--list", "目标一",
              "--type", "scope", "--list", "边界一", "边界二")
    goal = json.loads(skein_cli(ws, "prd", "read", "demo", "--type", "goal").stdout)["body"]
    scope = json.loads(skein_cli(ws, "prd", "read", "demo", "--type", "scope").stdout)["body"]
    assert "目标一" in goal and "边界二" not in goal, goal
    assert "边界一" in scope and "边界二" in scope, scope


# ── 全局 --pretty 渲染 ──────────────────────────────────────────────────────
def test_strip_global_flags_pretty() -> None:
    """-p/--pretty 是全局 flag: strip 出四元组, argv 中移除。"""
    from skeinlib.cli.main import _strip_global_flags
    argv, dbg, js, pretty = _strip_global_flags(["list", "--pretty", "-j"])
    assert argv == ["list"] and dbg is False and js is True and pretty is True
    argv, _, _, pretty = _strip_global_flags(["task", "show", "demo"])
    assert argv == ["task", "show", "demo"] and pretty is False


def test_pretty_value_renders_nested() -> None:
    """_pretty_value: dict 多行 / list 分块 / None-dash / bool 勾叉。"""
    from skeinlib.cli.main import _pretty_value
    assert _pretty_value(None) == "[dim]-[/dim]"
    assert _pretty_value(True) == "[green]✓[/green]"
    assert _pretty_value(False) == "[dim]✗[/dim]"
    assert _pretty_value("x") == "x"
    assert _pretty_value([]) == "[dim](空)[/dim]"
    d = _pretty_value({"a": 1, "b": {"c": 2}})
    assert "a" in d and "b" in d and "c" in d and "\n" in d  # 嵌套换行
    lst = _pretty_value([{"id": "t1"}, {"id": "t2"}])
    assert "t1" in lst and "t2" in lst and "─" in lst  # 条目分隔线
    assert _pretty_value([1, 2, "a"]) == "1, 2, a"  # 标量列表直连


def test_pretty_print_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    """_pretty_print 面板渲染冒烟: 不炸 + 标题 + key 可见。"""
    from skeinlib.cli.main import _pretty_print
    _pretty_print("list", {"tasks": [{"id": "demo"}], "count": 1})
    out = capsys.readouterr().out
    assert "skein list" in out and "tasks" in out and "demo" in out
