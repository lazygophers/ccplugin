"""spec.py 测试 — init/sediment/recall/inject-core/session-start/subagent-start/reindex/backlinks/orphan。

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
                  for p in (rules / "core").rglob("*.md")
                  if p.name not in ("index.md", "backlinks.md")]
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


def test_recall_fts5_and_grep_fallback(mem_ws: Path, mem_cli: MemCli) -> None:
    """recall 优先 FTS5 BM25 (reindex 生成 .recall.db); 删 db → grep fallback 仍命中不崩。"""
    body = _write_body(mem_ws, "b1.md", "pnpm workspace 装包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build",
            "--title", "pnpm workspace 装包", "--keywords", "pnpm,workspace",
            "--source", "t02", "--body-file", str(body))

    db = mem_ws / ".skein" / "spec" / ".recall.db"
    assert db.exists(), "reindex 未生成 .recall.db"

    # FTS5 BM25 路径 (OR 兼容中文: 'pnpm' 命中即召回, '装依赖' 分词对不上 '装包' 无碍)
    out = mem_cli(mem_ws, "recall", "pnpm 装依赖").stdout
    assert "pnpm" in out and "t02-00.md" in out, f"FTS5 未命中: {out}"
    assert "BM25" in out, f"未走 FTS5 路径: {out}"

    # 删 .recall.db → grep fallback 仍命中且不崩
    db.unlink()
    out2 = mem_cli(mem_ws, "recall", "pnpm").stdout
    assert "pnpm" in out2 and "t02-00.md" in out2, f"grep fallback 未命中: {out2}"
    assert "fallback" in out2, f"未走 grep fallback: {out2}"

    # 含双引号的 query → 提前降级 grep (不触发 MATCH 语法错)
    out3 = mem_cli(mem_ws, "recall", 'p"npm').stdout
    assert "recall" in out3, "含双引号 query 不该崩"


def test_backlinks_rebuild(mem_ws: Path, mem_cli: MemCli) -> None:
    """A-MEM-lite 反链: A body 写 [[B-stem]] → reindex 产 recall/backlinks.md, B 章节列 A 反链。"""
    # 先存 B (stem = t02-00), 再存 A (stem = t01-01, 层内 seq 全局递增) body 引用 B
    body_b = _write_body(mem_ws, "b.md", "pnpm workspace 装包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build",
            "--title", "pnpm 装包", "--keywords", "pnpm", "--source", "t02",
            "--body-file", str(body_b))
    body_a = _write_body(mem_ws, "a.md", "装依赖见 [[t02-00]]。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build",
            "--title", "依赖流程", "--keywords", "deps", "--source", "t01",
            "--body-file", str(body_a))

    bl = mem_ws / ".skein" / "spec" / "recall" / "backlinks.md"
    assert bl.exists(), "reindex 未产 recall/backlinks.md"
    txt = bl.read_text()
    assert "## t02-00" in txt, f"backlinks 缺 B 章节 (反链目标): {txt}"
    assert "recall/build/t01-01" in txt, f"backlinks 缺 A 反链 (referrer): {txt}"


def test_orphan_detection(mem_ws: Path, mem_cli: MemCli) -> None:
    """孤立判据: 无入度 + active + created 超 STALE_DAYS → maintain 报 [孤立], --apply 归档。"""
    import re
    import time

    body = _write_body(mem_ws, "b.md", "孤立规则正文, 无 wikilink 入度。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git",
            "--title", "孤立规则", "--keywords", "orphan", "--source", "t01",
            "--body-file", str(body))
    # 改老 created (> STALE_DAYS=180); updated 保留新 — 排除 stale 误判, 只剩孤立信号
    rule = mem_ws / ".skein" / "spec" / "core" / "git" / "t01-00.md"
    old_ts = str(int(time.time()) - 200 * 86400)
    rule.write_text(re.sub(r"^created: \d+", f"created: {old_ts}",
                           rule.read_text(), flags=re.MULTILINE))
    mem_cli(mem_ws, "reindex")

    out = mem_cli(mem_ws, "maintain").stdout
    assert "[孤立]" in out and "t01-00" in out, f"maintain 未报孤立: {out}"

    out_apply = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert not rule.exists(), f"--apply 未归档孤立规则: {out_apply}"
    assert "prune-orphan" in out_apply, f"--apply 缺 prune-orphan 审计: {out_apply}"


def test_external_layer(mem_ws: Path, mem_cli: MemCli) -> None:
    """external 层: sediment --layer external 写盘; recall 跨层 FTS5 命中带 [external];
    顶层 index 含 external 行; maintain 扫 external (stale 对 external 生效);
    degrade external/... 拒 (终点层)。"""
    rules = mem_ws / ".skein" / "spec"

    # 1. sediment --layer external 写盘
    body = _write_body(mem_ws, "ext.md", "外部依赖: vue3 组合式 API 用 setup。")
    mem_cli(mem_ws, "sediment", "--layer", "external", "--category", "docs",
            "--title", "vue3 setup", "--keywords", "vue,setup", "--source", "ext01",
            "--body-file", str(body))
    ext_file = rules / "external" / "docs" / "ext01-00.md"
    assert ext_file.exists(), f"external 写盘失败: {ext_file}"

    # 2. recall 跨层命中 external, 带 [external] 标识
    out = mem_cli(mem_ws, "recall", "vue setup").stdout
    assert "[external]" in out and "ext01-00.md" in out, f"recall 未跨层命中 external: {out}"

    # 3. 顶层 index.md 含 external 行
    top = (rules / "index.md").read_text()
    assert "| external |" in top, f"顶层索引缺 external 行: {top}"

    # 4. maintain 默认扫三层 (external 文件新鲜 → 不报 stale, 但 list 含 external)
    list_out = mem_cli(mem_ws, "list").stdout
    assert "[external]" in list_out and "ext01-00.md" in list_out, f"list 缺 external: {list_out}"

    # 5. maintain 对 external 生效: 改老 created+updated → 报 [stale] external/...
    import re
    import time
    old_ts = str(int(time.time()) - 200 * 86400)
    new_txt = ext_file.read_text()
    new_txt = re.sub(r"^created: \d+", f"created: {old_ts}", new_txt, flags=re.MULTILINE)
    new_txt = re.sub(r"^updated: \d+", f"updated: {old_ts}", new_txt, flags=re.MULTILINE)
    ext_file.write_text(new_txt)
    mem_cli(mem_ws, "reindex")
    mout = mem_cli(mem_ws, "maintain").stdout
    assert "[stale]" in mout and "external/docs/ext01-00" in mout, f"maintain 未扫 external stale: {mout}"

    # 6. degrade external/<cat>/<name> 拒 (终点层) — 直跑 subprocess 取 returncode (fixture 强 check=True)
    dgr = subprocess.run([sys.executable, str(MEM), "degrade", "external/docs/ext01-00"],
                         cwd=mem_ws, capture_output=True, text=True)
    assert dgr.returncode != 0, f"degrade external 不该成功: {dgr.stdout}"
    assert "终点层" in dgr.stderr, f"degrade 拒绝提示缺终点层: {dgr.stderr}"


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
    for fn in (test_init_sediment_index, test_recall_and_inject_core, test_hook_inject_session_and_subagent,
               test_recall_fts5_and_grep_fallback, test_backlinks_rebuild, test_orphan_detection,
               test_external_layer):
        fn(_mk_ws(), mem_cli)
    print("spec.py 测试全过 (init/sediment+三层索引/recall FTS5+grep fallback/inject-core隔离层/hook注入/backlinks/孤立/external层)")
