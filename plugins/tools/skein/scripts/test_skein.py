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
        # retain_days=0 → finish 即归档 (测归档链路; 默认 7 天惰性归档不便冒烟)
        cfg = d / ".skein/config.yaml"
        cfg.write_text(cfg.read_text().replace("retain_days: 7", "retain_days: 0"))

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
        sk(d, "subtask", "add", "task-1", "s1", "--name", "核心逻辑", "--desc", "描述", "--agent", "general-purpose")

        # start task-1 → worktree 建出
        sk(d, "start", "task-1")
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

        # 并发上限: create+start task-2, task-3 应被拒
        sk(d, "create", "task-2", "--name", "第二个", "--desc", "描述")
        sk(d, "subtask", "add", "task-2", "s1", "--name", "x", "--desc", "描述", "--agent", "general-purpose")
        sk(d, "start", "task-2")
        sk(d, "create", "task-3", "--name", "第三个", "--desc", "描述")
        sk(d, "subtask", "add", "task-3", "s1", "--name", "x", "--desc", "描述", "--agent", "general-purpose")
        r = sk(d, "start", "task-3", check=False)
        assert r.returncode != 0 and "并发上限" in r.stderr, "并发上限未生效"

        # 在 worktree 改文件 → finish 合并回主
        (wt / "feature.txt").write_text("done\n")
        sk(d, "finish", "task-1")
        assert (d / "feature.txt").exists(), "finish 未合并回主工作区"
        assert list((d / ".skein/task/archive").glob("*/*/task-1")), "未归档 (日期分层)"
        assert not (d / ".skein/task/task-1").exists(), "归档后 task 残留"
        assert not wt.exists(), "worktree 未销"
        # 归档后顶层 tasks 索引去掉 task-1
        top = json.loads((d / ".skein/task.json").read_text())
        assert not any(x["id"] == "task-1" for x in top["tasks"]), "归档 task 仍留在顶层索引"
        assert any(x["id"] == "task-2" for x in top["tasks"]), "task-2 应仍在顶层索引"

        # deps: task-3 依赖 task-2, task-2 未 finish 前 start task-3 (需先腾并发位)
        # task-1 已 finish, active=task-2, 上限2 → 可 start task-3 但 deps 阻塞
        (d / ".skein/task/task-3/task.json").write_text(
            json.dumps({**json.loads((d / ".skein/task/task-3/task.json").read_text()),
                        "deps": ["task-2"]}, ensure_ascii=False))
        r = sk(d, "start", "task-3", check=False)
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

        # task 级 ready: active 空 + task-3 前置(task-2)已归档→视完成 → task-3 就绪
        rout = sk(d, "ready").stdout
        assert "task-3" in rout and "就绪 task" in rout, f"ready 未列就绪 task-3: {rout!r}"

        # 多 active 并行: task-3 (dep task-2 已归档→视完成) 与 task-4 可同时 active
        sk(d, "start", "task-3")
        sk(d, "create", "task-4", "--name", "第四个", "--desc", "描述")
        sk(d, "subtask", "add", "task-4", "s1", "--name", "x", "--desc", "描述", "--agent", "general-purpose")
        sk(d, "start", "task-4")
        top = json.loads((d / ".skein/task.json").read_text())
        act = {x["id"] for x in top["tasks"] if x["status"] == "进行中"}
        assert act == {"task-3", "task-4"}, f"多 active 并行失效: {act}"
        sk(d, "finish", "task-3")
        top = json.loads((d / ".skein/task.json").read_text())
        assert any(x["id"] == "task-4" and x["status"] == "进行中" for x in top["tasks"]), "finish 误伤无关 active"

        # ---- subtask DAG 调度 ----
        sk(d, "create", "task-5", "--name", "编排任务", "--desc", "描述")
        sk(d, "subtask", "add", "task-5", "s1", "--name", "x", "--desc", "描述", "--agent", "general-purpose")
        sk(d, "subtask", "add", "task-5", "s2", "--name", "y", "--desc", "描述", "--agent", "general-purpose")
        sk(d, "subtask", "add", "task-5", "s3", "--deps", "s1,s2", "--name", "z", "--desc", "描述", "--agent", "general-purpose")
        assert (d / ".skein/task/task-5/task.md").exists(), "per-task 看板缺失"
        r = sk(d, "subtask", "ready", "task-5").stdout
        assert "s1" in r and "s2" in r and "s3" not in r, "就绪批错 (s3 应被依赖挡)"
        # ready 只读: 不改状态
        subs0 = json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"]
        assert all(s["status"] == "待处理" for s in subs0), "ready 误改状态 (应只读)"
        # claim 一次性认领整个就绪批 → s1/s2 标 running
        r = sk(d, "subtask", "claim", "task-5").stdout
        assert "s1" in r and "s2" in r, "claim 未返回就绪批"
        subs_c = json.loads((d / ".skein/task/task-5/task.json").read_text())["subtasks"]
        st = {s["sid"]: s["status"] for s in subs_c}
        assert st["s1"] == "运行中" and st["s2"] == "运行中", "claim 未标 running"
        # 时间戳: add→created, claim→started, done→finished
        s1 = next(s for s in subs_c if s["sid"] == "s1")
        assert isinstance(s1["created"], int) and isinstance(s1["started"], int), "subtask created/started 未记"
        assert s1["finished"] is None, "未 done 不应有 finished"
        # 满槽 (max_parallel=2) → start 第三个应报错
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
        # ---- pop: 只读提取一个可执行 (task, subtask) 对 ----
        # task-4 仍 active 且 s1 就绪 → pop 主路径返回 (task-4, s1)
        rp = sk(d, "pop").stdout
        assert "task-4" in rp and "s1" in rp, f"pop 未提取到 active task 就绪 subtask: {rp!r}"
        # pop 只读: 不改状态
        s4 = json.loads((d / ".skein/task/task-4/task.json").read_text())["subtasks"]
        assert {s["sid"]: s["status"] for s in s4}["s1"] == "待处理", "pop 误改状态 (应只读)"
        # 无 active 就绪 + 有就绪 pending 时走 "待激活" 提示 (task-5 pending, task-4 done 掉 s1 后腾出)
        sk(d, "subtask", "claim", "task-4"); sk(d, "subtask", "done", "task-4", "s1"); sk(d, "finish", "task-4")
        assert "待激活" in sk(d, "pop").stdout, "pop 未提示就绪 pending task"

    test_setup()
    test_lock()
    test_multirepo()
    print("skein.py 冒烟测试全过 (init/create/start/finish/并发上限/deps门/看板/archive清理/多active并行/subtask-DAG/setup迁移/多子git worktree)")


def test_lock():
    # 写锁: 持锁时另一获取者应阻塞到超时 → SystemExit
    import importlib.util
    spec = importlib.util.spec_from_file_location("skein_l", SKEIN)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory() as d:
        lp = Path(d) / ".lock"
        with m._workspace_lock(lp, timeout=1.0):
            try:
                with m._workspace_lock(lp, timeout=0.2):
                    raise AssertionError("持锁时不应拿到第二把锁")
            except SystemExit:
                pass  # 预期: 超时 SystemExit
        # 释放后可重新获取
        with m._workspace_lock(lp, timeout=0.2):
            pass


def test_multirepo():
    # 多子 git: 非 git 父目录下两并列 repo, task 声明 --repos → start 各建 worktree, finish 各自合入
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for r in ("repoA", "repoB"):
            sub = d / r
            sub.mkdir()
            git(sub, "init", "-q")
            git(sub, "config", "user.email", "t@t.dev")
            git(sub, "config", "user.name", "t")
            (sub / "f.txt").write_text(f"base-{r}\n")
            git(sub, "add", "-A"); git(sub, "commit", "-qm", "init")
        sk(d, "init")
        sk(d, "create", "feat", "--name", "跨仓", "--desc", "改两仓", "--repos", "repoA,repoB")
        rl = sk(d, "repos", "feat").stdout
        assert "repoA" in rl and "repoB" in rl, rl
        sk(d, "subtask", "add", "feat", "s1", "--name", "改A", "--desc", "d", "--agent", "skein-executor")
        sk(d, "start", "feat")
        wa = d / ".worktrees/skein-feat/repoA"
        wb = d / ".worktrees/skein-feat/repoB"
        assert wa.is_dir() and wb.is_dir(), "多子 git worktree 未建全"
        # 各 worktree 内改文件并提交前留给 finish 提交
        (wa / "f.txt").write_text("base-repoA\nchangeA\n")
        (wb / "f.txt").write_text("base-repoB\nchangeB\n")
        sk(d, "finish", "feat")
        assert "changeA" in (d / "repoA/f.txt").read_text(), "repoA 未合入"
        assert "changeB" in (d / "repoB/f.txt").read_text(), "repoB 未合入"
        # worktree 与分支清理
        assert not wa.exists() and not wb.exists(), "worktree 未销"
        for r in ("repoA", "repoB"):
            br = subprocess.run(["git", "branch", "--list", "skein/feat"], cwd=d / r,
                                capture_output=True, text=True).stdout
            assert "skein/feat" not in br, f"{r} 分支未删"


def test_setup():
    # 新仓 setup: 无 trellis → 建本地 spec, manifest trellis_present=false
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")
        m = json.loads(sk(d, "setup").stdout)
        assert m["trellis_present"] is False and m["spec_needs_reorg"] is False, m
        assert (d / ".skein/spec").is_dir() and not (d / ".skein/spec").is_symlink(), "本地 spec 未建"

    def _mk_trellis(d):
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

    def _assert_migrated(d, m, mode):
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
        assert tj["name"] == "任务X" and tj["status"] == "待处理", ("task.json 未翻译为 skein schema", tj)
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
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")
        _mk_trellis(d)
        m = json.loads(sk(d, "setup").stdout)
        _assert_migrated(d, m, "compat")
        assert (d / ".trellis/spec/git.md").exists(), "兼容模式误删 .trellis 数据"
        assert not (d / ".trellis/hooks").exists(), "兼容模式未删 trellis 接线"
        assert m["trellis_removed"] is False, m

    # --full 模式: 兼容全套 + 整删 .trellis
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")
        _mk_trellis(d)
        m = json.loads(sk(d, "setup", "--full").stdout)
        _assert_migrated(d, m, "full")
        assert not (d / ".trellis").exists(), "--full 未整删 .trellis"
        assert m["trellis_removed"] is True, m


if __name__ == "__main__":
    main()
