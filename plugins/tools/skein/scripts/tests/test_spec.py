"""spec.py 测试 — init/sediment/recall/inject-core/session-start/subagent-start/reindex。

通过 subprocess 跑 spec.py CLI (conftest 的 mem_ws fixture 造隔离 .skein/spec/ 仓),
覆盖三条核心路径:
  1. init 建 spec 骨架 + sediment 写盘 + 三层索引同步 (layer/category/top) + 跨类目 seq 递增 + reindex 幂等。
  2. recall 粗筛 (命中/无命中) + inject-core 隔离层 (core 全文 / 去 frontmatter / 不混 recall)。
  3. hook 注入: session-start 只出极简索引 + 合法 hook JSON; subagent-start 注 core 全文 + spec 纪律。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

MEM: Path = Path(__file__).resolve().parent.parent / "spec.py"

MemCli = Callable[..., subprocess.CompletedProcess[str]]


def test_init_sediment_index(mem_ws: Path, mem_cli: MemCli) -> None:
    """init 建 spec 骨架; sediment core 写盘 + 三层 index 同步 + 跨类目 seq 递增 + reindex 幂等。"""
    rules = mem_ws / ".skein" / "spec"
    assert (rules / "core/index.md").exists() and (rules / "recall/index.md").exists()
    assert (rules / "index.md").exists(), "顶层总索引缺失"

    body = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--title", "合并冲突处理",
            "--keywords", "merge,conflict,worktree", "--source", "t01", "--body-file", str(body))
    core_files = [p.relative_to(rules / "core").as_posix()
                  for p in (rules / "core").rglob("*.md") if p.name != "index.md"]
    assert core_files == ["git/t01-00.md"], core_files
    assert "合并冲突处理" in (rules / "core/index.md").read_text(), "core index 未同步"
    assert "git" in (rules / "index.md").read_text(), "顶层索引未含类目"

    # 跨类目 seq 全局递增: 第二次沉淀到 style, 序号仍 +1 (不重置)
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "style", "--title", "命名规范",
            "--keywords", "naming", "--source", "t03", "--body-file", str(body))
    rows = _rule_rows(rules / "core/index.md")
    assert len(rows) == 2, f"预期 2 行 core 规则得 {len(rows)}"
    assert (rules / "core/style/t03-01.md").exists(), "跨类目 seq 未递增"

    # reindex 幂等: 行数不变
    mem_cli(mem_ws, "reindex")
    assert len(_rule_rows(rules / "core/index.md")) == 2, "reindex 后行数变了"


def test_recall_and_inject_core(mem_ws: Path, mem_cli: MemCli) -> None:
    """recall 粗筛命中/无命中; inject-core 输出 core 全文, 去 frontmatter, 不混 recall。"""
    body_c = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--title", "合并冲突处理",
            "--keywords", "merge,conflict", "--source", "t01", "--body-file", str(body_c))
    body_r = _write_body(mem_ws, "b2.md", "pnpm workspace 加包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build", "--title", "pnpm workspace 装包",
            "--keywords", "pnpm,workspace,install", "--source", "t02", "--body-file", str(body_r))

    out = mem_cli(mem_ws, "recall", "pnpm 装依赖").stdout
    assert "pnpm" in out and "t02-00.md" in out, f"recall 未命中: {out}"
    assert "无命中" in mem_cli(mem_ws, "recall", "无关词汇xyz").stdout, "无关 query 不该命中"

    inj = mem_cli(mem_ws, "inject-core").stdout
    assert "合并冲突必 abort" in inj, "inject-core 缺 core 正文"
    assert "authored-by" not in inj, "inject-core 未去 frontmatter"
    assert "pnpm" not in inj, "inject-core 混入 recall"


def test_hook_inject_session_and_subagent(mem_ws: Path, mem_cli: MemCli) -> None:
    """session-start 只注入极简索引 (标题+类目, 无正文) + 合法 hook JSON;
    subagent-start 注 core 全文 + spec 纪律指令。"""
    body = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--title", "合并冲突处理",
            "--keywords", "merge,conflict", "--source", "t01", "--body-file", str(body))

    ss = json.loads(mem_cli(mem_ws, "session-start").stdout)
    ctx = ss["hookSpecificOutput"]["additionalContext"]
    assert ss["hookSpecificOutput"]["hookEventName"] == "SessionStart", "hook 格式错"
    assert "合并冲突处理" in ctx, "索引缺规则标题"
    assert "合并冲突必 abort" not in ctx, "session-start 不该注入正文 (只索引)"
    assert "inject-core" in ctx, "索引未提示按需拉全文"

    sa = json.loads(mem_cli(mem_ws, "subagent-start").stdout)
    sctx = sa["hookSpecificOutput"]["additionalContext"]
    assert sa["hookSpecificOutput"]["hookEventName"] == "SubagentStart", "subagent hook 格式错"
    assert "合并冲突必 abort" in sctx, "subagent-start 该注入 core 正文 (非仅索引)"
    assert "SPEC:" in sctx and "recall" in sctx, "subagent-start 缺 spec 纪律指令"


def _write_body(d: Path, name: str, text: str) -> Path:
    p = d / name
    p.write_text(text)
    return p


def _rule_rows(index_md: Path) -> list[str]:
    return [l for l in index_md.read_text().splitlines()
            if l.startswith("| ") and "index" not in l and "---" not in l and "file" not in l]


def _mem(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """独立 CLI 跑 (__main__) — 无 fixture 时手造仓驱动 test_* 函数。"""
    return subprocess.run([sys.executable, str(MEM), *args], cwd=cwd,
                          capture_output=True, text=True, check=True)


class _MemCli:
    """直跑模式 (__main__) 的 mem_cli 替身: 同签名, 不依赖 pytest fixture。"""
    def __call__(self, cwd: Path, *args: str, inp: str | None = None) -> subprocess.CompletedProcess[str]:
        return _mem(cwd, *args)


if __name__ == "__main__":
    # 独立 CLI 跑 (无 pytest): 手造临时仓, 注入伪 fixture 驱动 test_* 函数。
    import tempfile

    def _mk_ws() -> Path:
        d = Path(tempfile.mkdtemp())
        for args in (("init", "-q"), ("config", "user.email", "t@t.dev"), ("config", "user.name", "t")):
            subprocess.run(["git", *args], cwd=d, check=True, capture_output=True)
        (d / "seed.txt").write_text("s\n")
        subprocess.run(["git", "add", "-A"], cwd=d, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=d, check=True, capture_output=True)
        _mem(d, "init")
        return d

    mem_cli = _MemCli()
    for fn in (test_init_sediment_index, test_recall_and_inject_core, test_hook_inject_session_and_subagent):
        fn(_mk_ws(), mem_cli)
    print("spec.py 测试全过 (init/sediment+三层索引/recall粗筛/inject-core隔离层/hook注入)")
