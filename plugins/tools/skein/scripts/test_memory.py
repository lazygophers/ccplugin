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

        # sediment core
        body = d / "b1.md"; body.write_text("finish 合并冲突必 abort, 禁强解。")
        mem(d, "sediment", "--layer", "core", "--title", "合并冲突处理",
            "--keywords", "merge,conflict,worktree", "--source", "t01", "--body-file", str(body))
        core_files = [p.name for p in (rules / "core").glob("*.md") if p.name != "index.md"]
        assert core_files == ["t01-00.md"], core_files
        assert "合并冲突处理" in (rules / "core/index.md").read_text(), "core index 未同步"

        # sediment recall
        body2 = d / "b2.md"; body2.write_text("pnpm workspace 加包后必跑 install。")
        mem(d, "sediment", "--layer", "recall", "--title", "pnpm workspace 装包",
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

        # 同名替换幂等
        mem(d, "sediment", "--layer", "core", "--title", "合并冲突处理 v2",
            "--keywords", "merge", "--source", "t01", "--body-file", str(body))
        # 第二次是新文件 t01-01 (seq 递增), 不同名; index 两行
        rows = [l for l in (rules / "core/index.md").read_text().splitlines() if l.startswith("| t01")]
        assert len(rows) == 2, f"预期 2 行 core 规则得 {len(rows)}"

    print("✅ memory.py 冒烟测试全过 (init/sediment/index同步/recall粗筛/inject-core去frontmatter+隔离层)")


if __name__ == "__main__":
    main()
