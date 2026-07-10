#!/usr/bin/env python3
"""memory.py 冒烟测试 — sediment 写盘 + index 同步 + recall 粗筛 + inject-core。"""
import subprocess
import sys
import tempfile
from pathlib import Path

MEM = Path(__file__).parent / "memory.py"


def mem(cwd, *args, inp=None):
    return subprocess.run([sys.executable, str(MEM), *args], cwd=cwd,
                          capture_output=True, text=True, check=True, input=inp)


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def main():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        git(d, "init", "-q")

        mem(d, "init")
        rules = d / ".claude/rules"
        assert (rules / "core/index.md").exists()
        assert (rules / "recall/index.md").exists()

        assert (rules / "index.md").exists(), "顶层总索引缺失"

        # sediment core (类目 git)
        body = d / "b1.md"; body.write_text("finish 合并冲突必 abort, 禁强解。")
        mem(d, "sediment", "--layer", "core", "--category", "git", "--title", "合并冲突处理",
            "--keywords", "merge,conflict,worktree", "--source", "t01", "--body-file", str(body))
        core_files = [p.relative_to(rules / "core").as_posix()
                      for p in (rules / "core").rglob("*.md") if p.name != "index.md"]
        assert core_files == ["git/t01-00.md"], core_files
        assert "合并冲突处理" in (rules / "core/index.md").read_text(), "core index 未同步"
        assert "git" in (rules / "index.md").read_text(), "顶层索引未含类目"

        # sediment recall (类目 build)
        body2 = d / "b2.md"; body2.write_text("pnpm workspace 加包后必跑 install。")
        mem(d, "sediment", "--layer", "recall", "--category", "build", "--title", "pnpm workspace 装包",
            "--keywords", "pnpm,workspace,install", "--source", "t02", "--body-file", str(body2))
        assert "pnpm" in (rules / "recall/index.md").read_text(), "recall index 未同步"

        # recall 粗筛命中
        out = mem(d, "recall", "pnpm 装依赖").stdout
        assert "pnpm" in out and "t02-00.md" in out, f"recall 未命中: {out}"
        out2 = mem(d, "recall", "无关词汇xyz").stdout
        assert "无命中" in out2, out2

        # inject-core 输出 core 正文, 不含 frontmatter, 不含 recall
        inj = mem(d, "inject-core").stdout
        assert "合并冲突必 abort" in inj, "inject-core 缺 core 正文"
        assert "authored-by" not in inj, "inject-core 未去 frontmatter"
        assert "pnpm" not in inj, "inject-core 混入 recall"

        # seq 层内全局递增: 第二次沉淀到不同类目 style, 序号仍 +1
        mem(d, "sediment", "--layer", "core", "--category", "style", "--title", "命名规范",
            "--keywords", "naming", "--source", "t03", "--body-file", str(body))
        rows = [l for l in (rules / "core/index.md").read_text().splitlines()
                if l.startswith("| ") and "index" not in l and "---" not in l and "file" not in l]
        assert len(rows) == 2, f"预期 2 行 core 规则得 {len(rows)}"
        assert (rules / "core/style/t03-01.md").exists(), "跨类目 seq 未递增"

        # reindex 幂等
        mem(d, "reindex")
        rows2 = [l for l in (rules / "core/index.md").read_text().splitlines()
                 if l.startswith("| ") and "index" not in l and "---" not in l and "file" not in l]
        assert len(rows2) == 2, f"reindex 后应仍 2 行得 {len(rows2)}"

    print("✅ memory.py 冒烟测试全过 (init/sediment×类目/顶层索引/recall粗筛/inject-core隔离层/reindex幂等)")


if __name__ == "__main__":
    main()
