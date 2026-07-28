"""spec.py 测试 — init/sediment/recall/inject-core/session-start/subagent-start/reindex/backlinks/orphan/restructure。

通过 subprocess 跑 spec.py CLI (conftest 的 mem_ws fixture 造隔离 .skein/spec/ 仓),
覆盖章节粒度模型 (文件夹=类目 / 文件=主题 / `## 标题`=单条规则):
  1. init 建 spec 骨架 + sediment 追加进主题文件 (同主题合并成一个文件) + 三层索引同步 + reindex 幂等。
  2. recall 粗筛 (FTS5 / grep fallback, 命中到 topic.md#标题) + inject-core 隔离层 (无时间元数据)。
  3. hook 注入: session-start 只出极简索引; subagent-start 注 core 全文 + spec 纪律。
  4. 关联: [[主题#规则标题]] 正反链; 新旧判定走文件 mtime (frontmatter 无时间字段)。
  5. restructure: 碎片文件按映射合并进主题文件, 源归档可 restore。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

MEM: Path = Path(__file__).resolve().parent.parent / "spec.py"

MemCli = Callable[..., subprocess.CompletedProcess[str]]


def test_init_sediment_index(mem_ws: Path, mem_cli: MemCli) -> None:
    """init 建 spec 骨架; sediment 追加为主题文件章节 — 同主题合并成一个文件, 不再一规则一文件。"""
    rules = mem_ws / ".skein" / "spec"
    assert (rules / "core/index.md").exists() and (rules / "recall/index.md").exists()
    assert (rules / "index.md").exists(), "顶层总索引缺失"

    body = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--topic", "merge",
            "--title", "合并冲突处理", "--keywords", "merge,conflict", "--body-file", str(body))
    body2 = _write_body(mem_ws, "b2.md", "共享分支禁 rebase。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--topic", "merge",
            "--title", "rebase 策略", "--keywords", "rebase", "--body-file", str(body2))

    core_files = [p.relative_to(rules / "core").as_posix()
                  for p in (rules / "core").rglob("*.md")
                  if p.name not in ("index.md", "backlinks.md")]
    assert core_files == ["git/merge.md"], f"同主题未合并进一个文件: {core_files}"
    txt = (rules / "core/git/merge.md").read_text()
    assert "## 合并冲突处理" in txt and "## rebase 策略" in txt, f"两条规则未各成章节: {txt}"
    assert "merge" in txt and "rebase" in txt, "keywords 未并入"
    for k in ("created:", "updated:", "source:", "authored-by:"):
        assert k not in txt, f"frontmatter 残留废弃字段 {k}"

    assert "合并冲突处理" in (rules / "core/index.md").read_text(), "core index 未同步"
    assert "git" in (rules / "index.md").read_text(), "顶层索引未含类目"

    # 索引按章节粒度: 一个主题文件两条规则 = 两行
    rows = _rule_rows(rules / "core/index.md")
    assert len(rows) == 2, f"预期 2 行规则得 {len(rows)}: {rows}"

    # reindex 幂等: 行数不变
    mem_cli(mem_ws, "reindex")
    assert len(_rule_rows(rules / "core/index.md")) == 2, "reindex 后行数变了"

    # --topic 缺省 → 落到类目同名主题文件
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "style",
            "--title", "命名规范", "--keywords", "naming", "--body-file", str(body))
    assert (rules / "core/style/style.md").exists(), "--topic 缺省未回落类目同名主题"


def test_recall_and_inject_core(mem_ws: Path, mem_cli: MemCli) -> None:
    """recall 粗筛命中/无命中; inject-core 输出 core 全文, 去 frontmatter, 不混 recall。"""
    body_c = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--topic", "merge",
            "--title", "合并冲突处理", "--keywords", "merge,conflict", "--body-file", str(body_c))
    body_r = _write_body(mem_ws, "b2.md", "pnpm workspace 加包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build", "--topic", "pnpm",
            "--title", "pnpm workspace 装包", "--keywords", "pnpm,workspace,install",
            "--body-file", str(body_r))

    out = mem_cli(mem_ws, "recall", "pnpm 装依赖").stdout
    assert "pnpm.md#pnpm workspace 装包" in out, f"recall 未命中到章节: {out}"
    assert "无命中" in mem_cli(mem_ws, "recall", "无关词汇xyz").stdout, "无关 query 不该命中"

    inj = mem_cli(mem_ws, "inject-core").stdout
    assert "合并冲突必 abort" in inj, "inject-core 缺 core 正文"
    assert "layer:" not in inj and "keywords:" not in inj, "inject-core 未去 frontmatter"
    assert "pnpm" not in inj, "inject-core 混入 recall"


def test_hook_inject_session_and_subagent(mem_ws: Path, mem_cli: MemCli) -> None:
    """session-start 只注入极简索引 (标题+主题, 无正文) + 合法 hook JSON;
    subagent-start 注 core 全文 + spec 纪律指令。"""
    body = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--topic", "merge",
            "--title", "合并冲突处理", "--keywords", "merge,conflict", "--body-file", str(body))

    ss = json.loads(mem_cli(mem_ws, "session-start").stdout)
    ctx = ss["hookSpecificOutput"]["additionalContext"]
    assert ss["hookSpecificOutput"]["hookEventName"] == "SessionStart", "hook 格式错"
    assert "[git/merge] 合并冲突处理" in ctx, f"索引缺 主题/规则标题: {ctx}"
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
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build", "--topic", "pnpm",
            "--title", "pnpm workspace 装包", "--keywords", "pnpm,workspace",
            "--body-file", str(body))

    db = mem_ws / ".skein" / "spec" / ".recall.db"
    assert db.exists(), "reindex 未生成 .recall.db"

    # FTS5 BM25 路径 (OR 兼容中文: 'pnpm' 命中即召回, '装依赖' 分词对不上 '装包' 无碍)
    out = mem_cli(mem_ws, "recall", "pnpm 装依赖").stdout
    assert "pnpm.md#" in out, f"FTS5 未命中: {out}"
    assert "BM25" in out, f"未走 FTS5 路径: {out}"

    # 删 .recall.db → grep fallback 仍命中且不崩
    db.unlink()
    out2 = mem_cli(mem_ws, "recall", "pnpm").stdout
    assert "pnpm.md" in out2, f"grep fallback 未命中: {out2}"
    assert "fallback" in out2, f"未走 grep fallback: {out2}"

    # 含双引号的 query → 提前降级 grep (不触发 MATCH 语法错)
    out3 = mem_cli(mem_ws, "recall", 'p"npm').stdout
    assert "recall" in out3, "含双引号 query 不该崩"


def test_backlinks_rebuild(mem_ws: Path, mem_cli: MemCli) -> None:
    """A-MEM-lite 正反链: A body 写 [[主题#规则标题]] → backlinks.md 里 B 记 ← 入链, A 记 → 出链。"""
    body_b = _write_body(mem_ws, "b.md", "pnpm workspace 装包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build", "--topic", "pnpm",
            "--title", "pnpm 装包", "--keywords", "pnpm", "--body-file", str(body_b))
    body_a = _write_body(mem_ws, "a.md", "装依赖见 [[pnpm#pnpm 装包]]。")
    mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "build", "--topic", "deps",
            "--title", "依赖流程", "--keywords", "deps", "--body-file", str(body_a))

    bl = mem_ws / ".skein" / "spec" / "recall" / "backlinks.md"
    assert bl.exists(), "reindex 未产 recall/backlinks.md"
    txt = bl.read_text()
    assert "## build/pnpm.md#pnpm 装包" in txt, f"backlinks 缺 B 章节 (反链目标): {txt}"
    assert "← recall/build/deps.md#依赖流程" in txt, f"backlinks 缺 B 的入链: {txt}"
    assert "→ [[pnpm#pnpm 装包]]" in txt, f"backlinks 缺 A 的出链: {txt}"


def test_orphan_detection(mem_ws: Path, mem_cli: MemCli) -> None:
    """孤立判据: 无入度 + active + 最近修改超 STALE_DAYS (走文件 mtime) → maintain 报 [孤立], --apply 归档。"""
    body = _write_body(mem_ws, "b.md", "孤立规则正文, 无 wikilink 入度。")
    mem_cli(mem_ws, "sediment", "--layer", "core", "--category", "git", "--topic", "orphan",
            "--title", "孤立规则", "--keywords", "orphan", "--body-file", str(body))
    # frontmatter 已无时间字段 → 改文件 mtime 造老规则 (> STALE_DAYS=180)
    rule = mem_ws / ".skein" / "spec" / "core" / "git" / "orphan.md"
    _age(rule, 200)

    out = mem_cli(mem_ws, "maintain").stdout
    assert "[孤立]" in out and "orphan" in out, f"maintain 未报孤立: {out}"

    # 孤立判据含 age > STALE_DAYS → 必同时命中 stale, 归档审计理由取先命中的 prune-stale
    out_apply = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert not rule.exists(), f"--apply 未归档孤立规则: {out_apply}"
    assert "prune-" in out_apply and "orphan.md" in out_apply, f"--apply 缺归档审计: {out_apply}"


def test_restructure_merge(mem_ws: Path, mem_cli: MemCli) -> None:
    """restructure: 碎片文件按映射合并进主题文件 — 一个源文件 = 一条规则, 源归档后可 restore。"""
    rules = mem_ws / ".skein" / "spec"
    for i, (title, text) in enumerate([("变量命名", "# 小写下划线\n\n禁驼峰。"),
                                       ("函数命名", "动词开头。")]):
        b = _write_body(mem_ws, f"s{i}.md", text)
        mem_cli(mem_ws, "sediment", "--layer", "recall", "--category", "style",
                "--topic", f"frag-{i}", "--title", title, "--keywords", "naming",
                "--body-file", str(b))

    plan = mem_ws / "plan.json"
    plan.write_text(json.dumps({"recall/style/convention.md":
                                ["recall/style/frag-0.md", "recall/style/frag-1.md"]}))

    dry = mem_cli(mem_ws, "restructure", "--map", str(plan), "--dry-run").stdout
    assert "dry-run" in dry and (rules / "recall/style/frag-0.md").exists(), "dry-run 不该落盘"

    mem_cli(mem_ws, "restructure", "--map", str(plan))
    merged = rules / "recall/style/convention.md"
    txt = merged.read_text()
    assert "## 变量命名" in txt and "## 函数命名" in txt, f"未合并成两条规则: {txt}"
    assert "### 小写下划线" in txt, f"源正文一级标题未降级为 ###: {txt}"
    assert not (rules / "recall/style/frag-0.md").exists(), "源文件未归档"

    ts = sorted(p.name for p in (rules / ".archive").iterdir())[-1]
    mem_cli(mem_ws, "restore", ts)
    assert (rules / "recall/style/frag-0.md").exists(), "restore 未回滚源文件"


def test_external_layer(mem_ws: Path, mem_cli: MemCli) -> None:
    """external 层: sediment --layer external 写盘; recall 跨层 FTS5 命中带 [external];
    顶层 index 含 external 行; maintain 扫 external (stale 走 mtime);
    degrade external/... 拒 (终点层)。"""
    rules = mem_ws / ".skein" / "spec"

    # 1. sediment --layer external 写盘
    body = _write_body(mem_ws, "ext.md", "外部依赖: vue3 组合式 API 用 setup。")
    mem_cli(mem_ws, "sediment", "--layer", "external", "--category", "docs", "--topic", "vue",
            "--title", "vue3 setup", "--keywords", "vue,setup", "--body-file", str(body))
    ext_file = rules / "external" / "docs" / "vue.md"
    assert ext_file.exists(), f"external 写盘失败: {ext_file}"

    # 2. recall 跨层命中 external, 带 [external] 标识
    out = mem_cli(mem_ws, "recall", "vue setup").stdout
    assert "[external]" in out and "vue.md#vue3 setup" in out, f"recall 未跨层命中 external: {out}"

    # 3. 顶层 index.md 含 external 行
    top = (rules / "index.md").read_text()
    assert "| external |" in top, f"顶层索引缺 external 行: {top}"

    # 4. list 含 external
    list_out = mem_cli(mem_ws, "list").stdout
    assert "[external]" in list_out and "vue.md#vue3 setup" in list_out, f"list 缺 external: {list_out}"

    # 5. maintain 对 external 生效: 改老 mtime → 报 [stale] external/...
    _age(ext_file, 200)
    mout = mem_cli(mem_ws, "maintain").stdout
    assert "[stale]" in mout and "external/docs/vue" in mout, f"maintain 未扫 external stale: {mout}"

    # 6. degrade external/<cat>/<topic> 拒 (终点层) — 直跑 subprocess 取 returncode (fixture 强 check=True)
    dgr = subprocess.run([sys.executable, str(MEM), "degrade", "external/docs/vue"],
                         cwd=mem_ws, capture_output=True, text=True)
    assert dgr.returncode != 0, f"degrade external 不该成功: {dgr.stdout}"
    assert "终点层" in dgr.stderr, f"degrade 拒绝提示缺终点层: {dgr.stderr}"


def test_core_budget_from_config(mem_ws: Path) -> None:
    """core_budget() 读 .skein/config.yaml spec_core_budget (热改); 缺失/非正整数 → 默认 1000。"""
    script_dir = str(MEM.parent)

    def _budget() -> int:
        r = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {script_dir!r}); "
             "from spec import core_budget; print(core_budget())"],
            cwd=mem_ws, capture_output=True, text=True, check=True)
        return int(r.stdout.strip())

    # 缺 config → 默认 1000
    assert _budget() == 1000, "无 config 未返默认 1000"

    # 写 config.yaml → 读 500 (热改, 懒求值每次读盘)
    (mem_ws / ".skein" / "config.yaml").write_text("spec_core_budget: 500\n")
    assert _budget() == 500, "config spec_core_budget 未生效"

    # 非正整数 → 回落默认
    (mem_ws / ".skein" / "config.yaml").write_text("spec_core_budget: not-a-num\n")
    assert _budget() == 1000, "非数字值未回落默认 1000"


def _age(f: Path, days: int) -> None:
    """把文件 mtime 推老 days 天 (frontmatter 已无时间字段, 新旧判定只看 mtime/git)。"""
    old = time.time() - days * 86400
    os.utime(f, (old, old))


def _write_body(d: Path, name: str, text: str) -> Path:
    p = d / name
    p.write_text(text)
    return p


def _rule_rows(index_md: Path) -> list[str]:
    return [ln for ln in index_md.read_text().splitlines()
            if ln.startswith("| ") and not ln.startswith("| rule") and "---" not in ln]


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
               test_restructure_merge, test_external_layer,
               lambda ws, _cli: test_core_budget_from_config(ws)):  # 只收 ws, 无 cli
        fn(_mk_ws(), mem_cli)
    print("spec.py 测试全过 (init/sediment主题合并/recall FTS5+grep fallback/inject-core隔离层/"
          "hook注入/正反链/孤立/restructure/external层/core_budget config)")
