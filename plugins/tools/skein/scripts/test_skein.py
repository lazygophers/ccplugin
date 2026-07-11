#!/usr/bin/env python3
"""skein.py 冒烟测试 — 临时 git 仓跑 init→create→start→finish 全链。

无框架, 纯 assert。跑: python3 test_skein.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKEIN = Path(__file__).parent / "skein.py"


def sk(cwd, *args, check=True):
    return subprocess.run([sys.executable, str(SKEIN), *args], cwd=cwd,
                          capture_output=True, text=True, check=check)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def main():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")
        git(d, "config", "user.email", "t@t.dev")
        git(d, "config", "user.name", "t")
        (d / "seed.txt").write_text("seed\n")
        git(d, "add", "-A"); git(d, "commit", "-q", "-m", "seed")

        # init
        sk(d, "init")
        assert (d / ".skein" / "config.json").exists(), "config 缺失"
        assert (d / ".skein" / "task.md").exists(), "看板缺失"

        # create t01
        out = sk(d, "create", "第一个任务", "--desc", "测试").stdout.strip()
        tid = out.split("\t")[0]
        assert tid == "t01", f"预期 t01 得 {tid}"
        t = json.loads((d / ".skein/task/t01/task.json").read_text())
        assert t["status"] == "pending"
        assert t["contracts"] == [], "create 未初始化 contracts"

        # contract: --add 落盘 + 无参列出
        sk(d, "contract", "t01", "--add", "输出必须幂等")
        t = json.loads((d / ".skein/task/t01/task.json").read_text())
        assert t["contracts"] == ["输出必须幂等"], t["contracts"]
        assert "输出必须幂等" in sk(d, "contract", "t01").stdout, "contract 未列出"

        # journal: --add 带时间戳追加 + append-only 两条都在 + 无参列出
        sk(d, "journal", "--id", "t01", "--add", "拆出 3 个 subtask")
        sk(d, "journal", "--id", "t01", "--add", "完成核心逻辑")
        jout = sk(d, "journal", "--id", "t01").stdout
        assert "拆出 3 个 subtask" in jout and "完成核心逻辑" in jout, "journal append-only 未保全部条目"

        # start t01 → worktree 建出
        sk(d, "start", "t01")
        t = json.loads((d / ".skein/task/t01/task.json").read_text())
        assert t["status"] == "in_progress", t["status"]
        wt = Path(t["worktree"])
        assert wt.exists(), "worktree 未建"
        assert json.loads((d / ".skein/state.json").read_text())["focus"] == "t01"

        # journal 无 --id 用 focus
        sk(d, "journal", "--add", "start 后记录")
        assert "start 后记录" in sk(d, "journal").stdout, "journal focus 默认失效"

        # session-context: 有 active task → JSON envelope 含 task id
        r = sk(d, "session-context")
        assert r.returncode == 0 and "t01" in r.stdout, "session-context 未含 active task"
        payload = json.loads(r.stdout)
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart", "注入格式错"
        # 无 .skein/ 的临时目录 → 静默 exit 0 无输出
        with tempfile.TemporaryDirectory() as bare:
            git(Path(bare), "init", "-q")
            r2 = sk(Path(bare), "session-context")
            assert r2.returncode == 0 and r2.stdout.strip() == "", f"非 skein 项目应静默: {r2.stdout!r}"

        # 并发上限: create+start t02, t03 应被拒
        sk(d, "create", "第二个")
        sk(d, "start", "t02")
        sk(d, "create", "第三个")
        r = sk(d, "start", "t03", check=False)
        assert r.returncode != 0 and "并发上限" in r.stderr, "并发上限未生效"

        # 在 worktree 改文件 → finish 合并回主
        (wt / "feature.txt").write_text("done\n")
        sk(d, "finish", "t01")
        assert (d / "feature.txt").exists(), "finish 未合并回主工作区"
        assert list((d / ".skein/task/archive").glob("*/*/t01")), "未归档 (日期分层)"
        assert list((d / ".skein/task/archive").glob("*/*/t01/journal.md")), "journal 未随 task 归档"
        assert not (d / ".skein/task/t01").exists(), "归档后 task 残留"
        assert not wt.exists(), "worktree 未销"
        # focus 切到剩余 active t02
        assert json.loads((d / ".skein/state.json").read_text())["focus"] == "t02"

        # deps: t03 依赖 t02, t02 未 finish 前 start t03 (需先腾并发位)
        # t01 已 finish, active=t02, 上限2 → 可 start t03 但 deps 阻塞
        (d / ".skein/task/t03/task.json").write_text(
            json.dumps({**json.loads((d / ".skein/task/t03/task.json").read_text()),
                        "deps": ["t02"]}, ensure_ascii=False))
        r = sk(d, "start", "t03", check=False)
        assert r.returncode != 0 and "前置未完成" in r.stderr, "deps 门未生效"

        # board 渲染含 focus 标记
        board = (d / ".skein/task.md").read_text()
        assert "t02" in board and "⭐" in board, "看板缺 focus 标记"

        # archive in_progress task → 销 worktree/branch + 让出 focus (不泄漏)
        wt2 = Path(json.loads((d / ".skein/task/t02/task.json").read_text())["worktree"])
        assert wt2.exists()
        sk(d, "archive", "t02")
        assert not wt2.exists(), "archive 未销 worktree"
        br = subprocess.run(["git", "branch", "--list", "skein/t02"], cwd=d,
                            capture_output=True, text=True).stdout
        assert "skein/t02" not in br, "archive 未删 branch"
        assert json.loads((d / ".skein/state.json").read_text())["focus"] is None, "archive 未让出 focus"
        assert sk(d, "current", check=False).returncode == 0, "archive 后 current 崩溃"

        # finish 非 focus task 不抢占无关 active 的 focus
        sk(d, "start", "t03")  # t02 已归档, dep 视为完成 → 可 start
        sk(d, "create", "第四个"); sk(d, "start", "t04")
        assert json.loads((d / ".skein/state.json").read_text())["focus"] == "t04"
        sk(d, "finish", "t03")
        assert json.loads((d / ".skein/state.json").read_text())["focus"] == "t04", "finish 抢占无关 focus"

    print("✅ skein.py 冒烟测试全过 (init/create/start/finish/并发上限/deps门/看板/archive清理/focus不抢占)")


if __name__ == "__main__":
    main()
