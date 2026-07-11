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
        assert (d / ".skein" / "config.yaml").exists(), "config 缺失"
        # mini YAML 解析器往返: 类型 (int/bool/str) + # 注释
        import importlib.util
        spec = importlib.util.spec_from_file_location("skein", SKEIN)
        sk_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(sk_mod)
        rt = sk_mod._yaml_load(sk_mod._yaml_dump(
            {"max_active": 2, "auto_commit": True, "worktree_root": ".worktrees"}))
        assert rt == {"max_active": 2, "auto_commit": True, "worktree_root": ".worktrees"}, rt
        assert sk_mod._yaml_load("max_active: 2  # 注释\nfoo: bar")["max_active"] == 2, "注释未剥离"
        assert (d / ".skein" / "task.md").exists(), "看板缺失"
        # .gitignore: .skein/ 忽略 task.md, 根 .gitignore 补 worktree_root
        assert "task.md" in (d / ".skein" / ".gitignore").read_text(), ".skein/.gitignore 未忽略 task.md"
        assert ".worktrees/" in (d / ".gitignore").read_text(), "根 .gitignore 未补 worktree_root"
        sk(d, "init")  # 幂等: 二次 init 不重复追加根 .gitignore
        assert (d / ".gitignore").read_text().count(".worktrees/") == 1, "worktree 忽略重复追加"

        # create: id 必填且为可读 slug
        out = sk(d, "create", "t01", "--name", "第一个任务", "--desc", "测试").stdout.strip()
        tid = out.split("\t")[0]
        assert tid == "t01", f"预期 t01 得 {tid}"
        t = json.loads((d / ".skein/task/t01/task.json").read_text())
        assert t["name"] == "第一个任务", t["name"]
        assert t["status"] == "待处理", t["status"]
        # 非法 id (非 slug) + 重复 id 均拒
        assert sk(d, "create", "订单接口", check=False).returncode != 0, "非 slug id 应拒"
        assert sk(d, "create", "t01", check=False).returncode != 0, "重复 id 应拒"
        assert t["contracts"] == [], "create 未初始化 contracts"
        assert isinstance(t["created"], int), "created 须为时间戳"

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
        assert t["status"] == "进行中", t["status"]
        assert not t["worktree"].startswith("/"), f"worktree 须相对: {t['worktree']}"
        wt = d / t["worktree"]  # 相对 project root → 拼绝对
        assert wt.exists(), "worktree 未建"
        top = json.loads((d / ".skein/task.json").read_text())
        assert "focus" not in top, "顶层不应再有 focus 字段"
        # 顶层 task.json 汇总全表: id/状态/deps/worktree
        t01row = next(x for x in top["tasks"] if x["id"] == "t01")
        assert t01row["status"] == "进行中" and t01row["worktree"] == t["worktree"], t01row

        # journal 须显式 --id (无 focus 默认)
        sk(d, "journal", "--id", "t01", "--add", "start 后记录")
        assert "start 后记录" in sk(d, "journal", "--id", "t01").stdout, "journal --id 失效"

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
        sk(d, "create", "t02", "--name", "第二个")
        sk(d, "start", "t02")
        sk(d, "create", "t03", "--name", "第三个")
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
        # 归档后顶层 tasks 索引去掉 t01
        top = json.loads((d / ".skein/task.json").read_text())
        assert not any(x["id"] == "t01" for x in top["tasks"]), "归档 task 仍留在顶层索引"
        assert any(x["id"] == "t02" for x in top["tasks"]), "t02 应仍在顶层索引"

        # deps: t03 依赖 t02, t02 未 finish 前 start t03 (需先腾并发位)
        # t01 已 finish, active=t02, 上限2 → 可 start t03 但 deps 阻塞
        (d / ".skein/task/t03/task.json").write_text(
            json.dumps({**json.loads((d / ".skein/task/t03/task.json").read_text()),
                        "deps": ["t02"]}, ensure_ascii=False))
        r = sk(d, "start", "t03", check=False)
        assert r.returncode != 0 and "前置未完成" in r.stderr, "deps 门未生效"

        # board 渲染无 focus 标记, 列出 active task 行
        board = (d / ".skein/task.md").read_text()
        assert "t02" in board, "看板缺 task 行"
        assert "focus:" not in board, "看板不应再有 focus footer"

        # archive in_progress task → 销 worktree/branch + 从顶层索引移除
        wt2 = d / json.loads((d / ".skein/task/t02/task.json").read_text())["worktree"]
        assert wt2.exists()
        sk(d, "archive", "t02")
        assert not wt2.exists(), "archive 未销 worktree"
        br = subprocess.run(["git", "branch", "--list", "skein/t02"], cwd=d,
                            capture_output=True, text=True).stdout
        assert "skein/t02" not in br, "archive 未删 branch"
        top = json.loads((d / ".skein/task.json").read_text())
        assert not any(x["id"] == "t02" for x in top["tasks"]), "archive 未从顶层索引移除"
        assert sk(d, "current", check=False).returncode == 0, "archive 后 current 崩溃"

        # task 级 ready: active 空 + t03 前置(t02)已归档→视完成 → t03 就绪
        rout = sk(d, "ready").stdout
        assert "t03" in rout and "就绪 task" in rout, f"ready 未列就绪 t03: {rout!r}"

        # 多 active 并行: t03 (dep t02 已归档→视完成) 与 t04 可同时 active
        sk(d, "start", "t03")
        sk(d, "create", "t04", "--name", "第四个"); sk(d, "start", "t04")
        top = json.loads((d / ".skein/task.json").read_text())
        act = {x["id"] for x in top["tasks"] if x["status"] == "进行中"}
        assert act == {"t03", "t04"}, f"多 active 并行失效: {act}"
        sk(d, "finish", "t03")
        top = json.loads((d / ".skein/task.json").read_text())
        assert any(x["id"] == "t04" and x["status"] == "进行中" for x in top["tasks"]), "finish 误伤无关 active"

        # ---- subtask DAG 调度 ----
        sk(d, "create", "t05", "--name", "编排任务")
        sk(d, "subtask", "add", "t05", "s1", "--write", "a/*.py")
        sk(d, "subtask", "add", "t05", "s2", "--write", "b/*.py")
        sk(d, "subtask", "add", "t05", "s3", "--deps", "s1,s2", "--write", "a/*.py")
        assert (d / ".skein/task/t05/task.md").exists(), "per-task 看板缺失"
        r = sk(d, "subtask", "ready", "t05").stdout
        assert "s1" in r and "s2" in r and "s3" not in r, "就绪批错 (s3 应被依赖挡)"
        # ready 只读: 不改状态
        subs0 = json.loads((d / ".skein/task/t05/task.json").read_text())["subtasks"]
        assert all(s["status"] == "待处理" for s in subs0), "ready 误改状态 (应只读)"
        # claim 一次性认领整个就绪批 → s1/s2 标 running
        r = sk(d, "subtask", "claim", "t05").stdout
        assert "s1" in r and "s2" in r, "claim 未返回就绪批"
        st = {s["sid"]: s["status"] for s in json.loads((d / ".skein/task/t05/task.json").read_text())["subtasks"]}
        assert st["s1"] == "运行中" and st["s2"] == "运行中", "claim 未标 running"
        # 满槽 (max_parallel=2) → start 第三个应报错
        assert sk(d, "subtask", "start", "t05", "s3", check=False).returncode != 0, "满槽未挡"
        assert "无就绪" in sk(d, "subtask", "claim", "t05").stdout, "满槽 claim 未阻塞"
        sk(d, "subtask", "done", "t05", "s1")
        sk(d, "subtask", "done", "t05", "s2")
        assert "s3" in sk(d, "subtask", "ready", "t05").stdout, "依赖全 done 后 s3 未就绪"
        # 写集冲突串行: s3(a/*.py) 与仍 running 的同写集不能并发 — 另建验证
        subs = json.loads((d / ".skein/task/t05/task.json").read_text())["subtasks"]
        assert {s["sid"]: s["status"] for s in subs}["s3"] == "待处理"

    print("skein.py 冒烟测试全过 (init/create/start/finish/并发上限/deps门/看板/archive清理/多active并行/subtask-DAG)")


if __name__ == "__main__":
    main()
