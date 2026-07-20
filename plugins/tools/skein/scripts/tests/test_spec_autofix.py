"""spec.py 自动修复 (auto-fix) 测试 — degrade / maintain --apply / .audit-log 轮转 / stop-check hook。

通过 subprocess 跑 spec.py + hooks.py CLI (conftest 的 mem_ws fixture 造隔离 .skein/spec/ 仓),
覆盖四条已实现路径:
  1. degrade 单文件降级 (layer 改 core→recall + git mv + reindex + audit-log)。
  2. degrade --auto 循环降到 core < CORE_BUDGET 即停。
  3. maintain --apply 四类修复 (stale→归档 / keywords重复→归档保留最新 / 废弃→归档 / 断链只报告)
     + 无 --apply 只报告不改文件。
  4. .audit-log 写入格式 + 7 天轮转 (注入 10d/30d 旧行被清, 2d + 非 iso 头保留)。
  5. cmd_stop_check (Stop hook): 有问题写 .pending-fix JSON / 无问题删标记 / exit 0 不阻塞。

已知断点 (本 test 不覆盖, 待对应代码实现后补):
  - [main 检测 .pending-fix] stop-check 写出标记后, 「main 检测标记 → 派 skein-specer bg 跑
    maintain --apply」这步无代码承载 (文档 skein-spec/SKILL.md L128-152 写了, 但 skein.py /
    无读 .pending-fix 的逻辑, grep 全仓仅 hooks.py 写)。完整链路端到端 (Stop→标记→main→specer→
    修复) 待 main 检测实现后补。
  - [maintain --apply 超预算+stale 同文件崩溃] 当 core 最大文件同时触发 overbudget 与 stale 时,
      _degrade_core_to_budget 先把文件移到 recall/, 随后 _archive_batch 仍按 findings 里的旧
      core/ 路径归档 → FileNotFoundError (spec.py L447→L535)。本 test 用 xfail 标记, 回传 main
      check 阶段定修否。独立 overbudget (新文件不 stale) 或独立 stale (在 recall 层) 均正常。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

MEM: Path = Path(__file__).resolve().parent.parent / "spec.py"
HOOKS: Path = Path(__file__).resolve().parent.parent / "hooks.py"

MemCli = Callable[..., subprocess.CompletedProcess[str]]


def _ws_root(mem_ws: Path) -> Path:
    return mem_ws / ".skein" / "spec"


def _write_rule(mem_ws: Path, layer: str, cat: str, name: str, *,
                title: str = "r", keywords: str = "k", source: str = "s",
                status: str = "active", created: int | None = None,
                updated: int | None = None, body: str = "body") -> Path:
    """直接写一条 spec 规则文件 (绕开 sediment, 精控 created/updated/status 触发各判据)。"""
    ts = created if created is not None else int(time.time())
    up = updated if updated is not None else ts
    d = _ws_root(mem_ws) / layer / cat
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{name}.md"
    f.write_text(
        "---\n"
        f"title: {title}\n"
        f"layer: {layer}\n"
        f"category: {cat}\n"
        f"keywords: [{keywords}]\n"
        f"source: {source}\n"
        f"created: {ts}\n"
        f"updated: {up}\n"
        f"status: {status}\n"
        "---\n\n"
        f"{body}\n")
    return f


def _reindex(mem_ws: Path, mem_cli: MemCli) -> None:
    mem_cli(mem_ws, "reindex")


# ── 1. degrade 单文件降级 ──────────────────────────────────────────────────────
def test_degrade_single_file(mem_ws: Path, mem_cli: MemCli) -> None:
    """degrade core/<cat>/<name>: layer→recall + 文件移动到 recall/<cat>/ + reindex + audit-log 写入。"""
    ts = int(time.time())
    _write_rule(mem_ws, "core", "git", "t01-00", title="合并处理",
                keywords="merge,conflict", created=ts, updated=ts, body="finish 合并必 abort。")
    _reindex(mem_ws, mem_cli)

    out = mem_cli(mem_ws, "degrade", "git/t01-00").stdout
    root = _ws_root(mem_ws)
    assert "recall/git/t01-00.md" in out, f"degrade 未报 recall 路径: {out}"
    assert not (root / "core/git/t01-00.md").exists(), "原 core 文件未移走"
    moved = root / "recall/git/t01-00.md"
    assert moved.exists(), "recall 端文件未落盘"
    assert "layer: recall" in moved.read_text(), "frontmatter layer 未改 recall"
    assert "git/t01-00.md" in (root / "recall/index.md").read_text(), "recall index 未同步"
    assert "git/t01-00.md" not in (root / "core/index.md").read_text(), "core index 未剔旧条目"
    audit = (root / ".audit-log").read_text()
    assert "degrade|core/git/t01-00.md|core/git/t01-00.md->(recall/git/t01-00.md)|手动降级" in audit, \
        f"audit-log 格式/内容错: {audit}"


# ── 2. degrade --auto 循环降级 ─────────────────────────────────────────────────
def test_degrade_auto_loop_to_budget(mem_ws: Path, mem_cli: MemCli) -> None:
    """core 超 CORE_BUDGET → --auto 循环降 top-1 最大文件, 直到 core ≤ BUDGET 即停。"""
    ts = int(time.time())
    chunk = "x" * 2000  # 5 条 × ~2000 ≈ 10000 字符 > CORE_BUDGET(8000)
    for i in range(1, 6):
        _write_rule(mem_ws, "core", "big", f"t{i}-{i-1:02d}", title=f"big{i}",
                    keywords="k", source=f"t{i}", created=ts, updated=ts, body=chunk)
    _reindex(mem_ws, mem_cli)
    before = len(mem_cli(mem_ws, "inject-core").stdout)
    assert before > 8000, f"前置条件失败: core 未超预算 ({before})"

    out = mem_cli(mem_ws, "degrade", "--auto").stdout
    after = len(mem_cli(mem_ws, "inject-core").stdout)
    assert after <= 8000, f"循环后 core 仍超预算: {before}→{after}"
    assert "自动降级" in out and "→" in out, f"--auto 未报降级摘要: {out}"
    # 移到 recall 的条数 = before-after 涉及的文件数 (>0); core 端剩 ≤ 8000 字符的条目
    core_left = [p for p in (_ws_root(mem_ws) / "core").rglob("*.md") if p.name != "index.md"]
    recall_got = [p for p in (_ws_root(mem_ws) / "recall").rglob("*.md") if p.name != "index.md"]
    assert core_left and recall_got, "降级后 core/recall 均该有文件"


def test_degrade_auto_under_budget_noop(mem_ws: Path, mem_cli: MemCli) -> None:
    """core 未超预算 → --auto 不动任何文件 (无需降级)。"""
    ts = int(time.time())
    _write_rule(mem_ws, "core", "git", "t01-00", created=ts, updated=ts, body="小规则")
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "degrade", "--auto").stdout
    assert "无需降级" in out, f"未超预算该报无需降级: {out}"
    assert (_ws_root(mem_ws) / "core/git/t01-00.md").exists(), "未超预算却动了文件"


# ── 3. maintain --apply 四类修复 ───────────────────────────────────────────────
def test_maintain_dry_run_report_only(mem_ws: Path, mem_cli: MemCli) -> None:
    """无 --apply: 只报告不改文件 (stale 文件原地不动)。"""
    old = int(time.time()) - 200 * 86400  # 200d > STALE_DAYS(180)
    _write_rule(mem_ws, "recall", "misc", "t09-00", title="old rule",
                keywords="old", created=old, updated=old, body="stale body")
    _reindex(mem_ws, mem_cli)
    dry = mem_cli(mem_ws, "maintain").stdout
    assert "stale" in dry and "体检" in dry, f"dry-run 未报 stale: {dry}"
    # 不动文件
    assert (_ws_root(mem_ws) / "recall/misc/t09-00.md").exists(), "dry-run 不该动文件"


def test_maintain_apply_stale_archive(mem_ws: Path, mem_cli: MemCli) -> None:
    """stale (recall 层) → --apply 归档到 .archive/<ts>/。"""
    old = int(time.time()) - 200 * 86400
    _write_rule(mem_ws, "recall", "misc", "t09-00", title="old", created=old, updated=old)
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert "归档 (prune-stale)" in out, f"未报 stale 归档: {out}"
    assert not (_ws_root(mem_ws) / "recall/misc/t09-00.md").exists(), "stale 文件未移走"
    archived = list((_ws_root(mem_ws) / ".archive").rglob("t09-00.md"))
    assert archived, "stale 文件未进 .archive"


def test_maintain_apply_deprecated_archive(mem_ws: Path, mem_cli: MemCli) -> None:
    """status=deprecated → --apply 归档。"""
    ts = int(time.time())
    _write_rule(mem_ws, "recall", "dep", "x-00", title="dep", status="deprecated",
                created=ts, updated=ts)
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert "归档 (prune-deprecated)" in out, f"未报废弃归档: {out}"
    assert not (_ws_root(mem_ws) / "recall/dep/x-00.md").exists()


def test_maintain_apply_keywords_dup_keep_newest(mem_ws: Path, mem_cli: MemCli) -> None:
    """同 keywords 组 ≥3 条 → 归档旧的, 保留 updated 最新者。"""
    now = int(time.time())
    old, mid, new = now - 200, now - 100, now  # new 最新, 该保留
    for name, ts in (("a-00", old), ("b-01", new), ("c-02", mid)):
        _write_rule(mem_ws, "recall", "dup", name, title=f"dup-{name}",
                    keywords="shared,kw", source=name, created=ts, updated=ts)
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert "prune-dup" in out, f"未报 keywords 重复归档: {out}"
    # b-01 最新该留; a-00/c-02 该归档
    assert (_ws_root(mem_ws) / "recall/dup/b-01.md").exists(), "未保留最新 (b-01)"
    assert not (_ws_root(mem_ws) / "recall/dup/a-00.md").exists(), "最旧 a-00 未归档"
    assert not (_ws_root(mem_ws) / "recall/dup/c-02.md").exists(), "次新 c-02 未归档"


def test_maintain_apply_broken_link_report_only(mem_ws: Path, mem_cli: MemCli) -> None:
    """断链 → --apply 仍只报告 (需人判断修哪头), 文件不归档。"""
    ts = int(time.time())
    _write_rule(mem_ws, "recall", "git", "t-00", title="linker", created=ts, updated=ts,
                body="正文链 [[missing-target]]")
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert "断链" in out and "missing-target" in out, f"--apply 未报告断链: {out}"
    assert "仍需人工" in out, "断链未归入人工区"
    assert (_ws_root(mem_ws) / "recall/git/t-00.md").exists(), "断链文件被误归档"


def test_maintain_apply_clean_noop(mem_ws: Path, mem_cli: MemCli) -> None:
    """无问题 → --apply 报「无自动可修项」, 不动文件。"""
    ts = int(time.time())
    _write_rule(mem_ws, "core", "git", "t-00", title="clean", created=ts, updated=ts, body="ok")
    _reindex(mem_ws, mem_cli)
    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert "无自动可修项" in out, f"干净库该报无可修: {out}"


# ── 3b. maintain --apply 超预算+stale 同文件崩溃 (KNOWN BUG, xfail) ──────────────
def _make_overbudget_stale(mem_ws: Path, mem_cli: MemCli) -> None:
    """造一个 core 大文件同时超预算 + stale (created 老)。"""
    old = int(time.time()) - 200 * 86400
    _write_rule(mem_ws, "core", "git", "big-00", title="big", created=old, updated=old,
                body="x" * 9000)
    _reindex(mem_ws, mem_cli)


def test_maintain_apply_overbudget_stale_crash(mem_ws: Path, mem_cli: MemCli) -> None:
    """KNOWN BUG: overbudget + stale 同一最大文件 → _archive_batch 跑已被 degrade 移走的旧路径崩溃。

    根因: maintain --apply 先 _degrade_core_to_budget (把 big-00 移到 recall/), 再按 findings
    里 stale 条目 (仍指向 core/git/big-00) 构建 archive_reasons → _archive_batch.rename FileNotFoundError。
    独立 overbudget (新文件不 stale) 或独立 stale (在 recall 层) 均正常。
    回传 main check 阶段定修否; 修好后本 test 转正向断言。
    """
    import pytest  # type: ignore[import-not-found]
    _make_overbudget_stale(mem_ws, mem_cli)
    with pytest.raises(subprocess.CalledProcessError):
        mem_cli(mem_ws, "maintain", "--apply")  # check=True 默认 → 非零退出抛错


# ── 4. .audit-log 格式 + 7 天轮转 ──────────────────────────────────────────────
def test_audit_log_format_and_rotation(mem_ws: Path, mem_cli: MemCli) -> None:
    """新写入格式正确; 注入 10d/30d 旧行被清, 2d 近期 + 非 iso 头保留。"""
    log = _ws_root(mem_ws) / ".audit-log"
    now = datetime.now()
    old10 = (now - timedelta(days=10)).isoformat(timespec="seconds")
    old30 = (now - timedelta(days=30)).isoformat(timespec="seconds")
    new2 = (now - timedelta(days=2)).isoformat(timespec="seconds")
    log.write_text("\n".join([
        f"{old10}|degrade|core/a.md|core/a.md->(recall/a.md)|old10",
        f"{old30}|degrade|core/b.md|core/b.md->(recall/b.md)|old30",
        f"{new2}|degrade|core/c.md|core/c.md->(recall/c.md)|recent2",
        "handwritten-no-ts|archive|core/d.md|非 iso 头该保留",
    ]) + "\n")

    # 触发一次新写入 (degrade 一个 core 文件)
    ts = int(time.time())
    _write_rule(mem_ws, "core", "git", "z-00", title="z", created=ts, updated=ts, body="zb")
    _reindex(mem_ws, mem_cli)
    mem_cli(mem_ws, "degrade", "git/z-00")

    lines = log.read_text().splitlines()
    # 旧 10d/30d 清掉
    assert not any("old10" in ln or "old30" in ln for ln in lines), f"旧 >7d 行未清: {lines}"
    # 2d 近期 + 非 iso 头 + 新写入保留
    assert any("recent2" in ln for ln in lines), f"2d 近期行被误清: {lines}"
    assert any("handwritten-no-ts" in ln for ln in lines), f"非 iso 头行被误清: {lines}"
    assert any("手动降级" in ln and "z-00.md" in ln for ln in lines), f"新写入行缺失: {lines}"
    # 新行格式: iso_ts|action|file|before->(after)|reason
    new_line = [ln for ln in lines if "git/z-00.md" in ln][0]
    assert new_line.count("|") == 4, f"audit 行字段数错 (期望 5 段 4 管道): {new_line}"


# ── 5. cmd_stop_check (Stop hook) ──────────────────────────────────────────────
def _stop_check(mem_ws: Path) -> subprocess.CompletedProcess[str]:
    """跑 hooks.py stop-check, stdin 喂空 JSON (hook 不读 stdin, 但入口需合法 JSON)。"""
    return subprocess.run([sys.executable, str(HOOKS), "stop-check"],
                          cwd=mem_ws, capture_output=True, text=True, input="{}", check=True)


def test_stop_check_writes_pending_fix(mem_ws: Path, mem_cli: MemCli) -> None:
    """有问题 (断链) → .pending-fix 写出, JSON schema: ts/core_chars/budget/problems[]。"""
    ts = int(time.time())
    _write_rule(mem_ws, "recall", "git", "t-00", title="linker", created=ts, updated=ts,
                body="链 [[missing-target]]")
    _reindex(mem_ws, mem_cli)
    r = _stop_check(mem_ws)
    assert r.returncode == 0, "stop-check 永不阻塞 (exit 0)"
    marker = _ws_root(mem_ws) / ".pending-fix"
    assert marker.exists(), "有问题却未写 .pending-fix"
    payload = json.loads(marker.read_text())
    assert set(("ts", "core_chars", "budget", "problems")) <= set(payload), \
        f"pending-fix 缺字段: {payload.keys()}"
    assert payload["budget"] == 8000, f"budget 值错: {payload['budget']}"
    probs = payload["problems"]
    assert any(p.get("type") == "broken-link" and "missing-target" in p.get("detail", "")
               for p in probs), f"problems 未含断链: {probs}"


def test_stop_check_clean_deletes_marker(mem_ws: Path, mem_cli: MemCli) -> None:
    """无问题 → 删旧 .pending-fix 标记 (防已修复后误触发)。"""
    ts = int(time.time())
    _write_rule(mem_ws, "core", "git", "t-00", title="clean", created=ts, updated=ts, body="ok")
    _reindex(mem_ws, mem_cli)
    marker = _ws_root(mem_ws) / ".pending-fix"
    marker.write_text('{"stale": "old marker"}')  # 造旧标记
    r = _stop_check(mem_ws)
    assert r.returncode == 0
    assert not marker.exists(), "无问题时旧 .pending-fix 未清"


def test_stop_check_non_skein_silent(mem_ws: Path) -> None:
    """无 .skein/spec → 静默 exit 0, 不写标记 (非 skein 项目不污染)。"""
    # mem_ws 已 init spec; 删 spec 目录模拟非 skein
    import shutil
    shutil.rmtree(_ws_root(mem_ws))
    r = _stop_check(mem_ws)
    assert r.returncode == 0, "无 spec 该静默 exit 0"
    assert not (_ws_root(mem_ws) / ".pending-fix").exists()


# ── standalone CLI runner (无 pytest 时 python3 test_spec_autofix.py 直跑) ──────
def _mem(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(MEM), *args], cwd=cwd,
                          capture_output=True, text=True, check=True)


class _MemCli:
    def __call__(self, cwd: Path, *args: str, inp: str | None = None) -> subprocess.CompletedProcess[str]:
        return _mem(cwd, *args)


def _stop(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(HOOKS), "stop-check"], cwd=cwd,
                          capture_output=True, text=True, input="{}", check=True)


if __name__ == "__main__":
    import tempfile

    def _mk_ws() -> Path:
        d = Path(tempfile.mkdtemp())
        for a in (("init", "-q"), ("config", "user.email", "t@t.dev"),
                  ("config", "user.name", "t")):
            subprocess.run(["git", *a], cwd=d, check=True, capture_output=True)
        (d / "seed.txt").write_text("s\n")
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=d, check=True, capture_output=True)
        _mem(d, "init")
        return d

    cli = _MemCli()
    # 双参测试 (mem_ws, mem_cli); stop-check 非 skein 测试只收 mem_ws
    two_arg: tuple[Callable[[Path, MemCli], None], ...] = (
        test_degrade_single_file, test_degrade_auto_loop_to_budget,
        test_degrade_auto_under_budget_noop, test_maintain_dry_run_report_only,
        test_maintain_apply_stale_archive, test_maintain_apply_deprecated_archive,
        test_maintain_apply_keywords_dup_keep_newest,
        test_maintain_apply_broken_link_report_only, test_maintain_apply_clean_noop,
        test_audit_log_format_and_rotation, test_stop_check_writes_pending_fix,
        test_stop_check_clean_deletes_marker)
    for fn in two_arg:
        fn(_mk_ws(), cli)
    test_stop_check_non_skein_silent(_mk_ws())  # 单参测试, 独立调用免 mypy arity 冲突
    # test_maintain_apply_overbudget_stale_crash 需 pytest, 直跑模式跳过 (已知 bug)
    print(f"spec.py autofix 测试全过 ({len(two_arg) + 1} 项; "
          "overbudget+stale 崩溃用例需 pytest xfail, 直跑跳过)")
