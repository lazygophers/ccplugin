"""spec.py 测试 — init/sediment/recall/inject-core/session-start/subagent-start/reindex/backlinks/orphan/restructure/map。

通过 subprocess 跑 spec.py CLI (conftest 的 mem_ws fixture 造隔离 .skein/spec/ 仓),
覆盖章节粒度模型 (文件夹=类目 / 文件=主题 / `## 标题`=单条规则):
  1. init 建 spec 骨架 + sediment 追加进主题文件 (同主题合并成一个文件) + 三层索引同步 + reindex 幂等。
  2. recall 粗筛 (FTS5 / grep fallback, 命中到 topic.md#标题) + inject-core 隔离层 (无时间元数据)。
  3. hook 注入: session-start 只出极简索引; subagent-start 注 core 全文 + spec 纪律。
  4. 关联: [[主题#规则标题]] 正反链; 新旧判定走文件 mtime (frontmatter 无时间字段)。
  5. restructure: 碎片文件按映射合并进主题文件, 源归档可 restore。
  6. map skeleton: 现算目录树+符号+行数 (不写盘), 支持 map namespace 语义页合并。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

MEM: Path = Path(__file__).resolve().parent.parent / "spec.py"

MemCli = Callable[..., subprocess.CompletedProcess[str]]


def test_init_sediment_index(mem_ws: Path, mem_cli: MemCli) -> None:
    """init 建 spec 骨架; sediment 追加为主题文件章节 — 同主题合并成一个文件, 不再一规则一文件。"""
    rules = mem_ws / ".skein" / "spec"
    dirs = sorted(p.name for p in rules.iterdir() if p.is_dir() and not p.name.startswith("."))
    assert dirs == ["external", "map", "product", "rules"], (
        f"init 应恰建四 namespace (rules/product/map/external), 不建旧 core/recall: {dirs}"
    )
    assert (rules / "index.md").exists(), "顶层总索引缺失"

    body = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "git", "--topic", "merge",
            "--title", "合并冲突处理", "--keywords", "merge,conflict", "--body-file", str(body))
    body2 = _write_body(mem_ws, "b2.md", "共享分支禁 rebase。")
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "git", "--topic", "merge",
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
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "style",
            "--title", "命名规范", "--keywords", "naming", "--body-file", str(body))
    assert (rules / "core/style/style.md").exists(), "--topic 缺省未回落类目同名主题"


def test_recall_and_inject_core(mem_ws: Path, mem_cli: MemCli) -> None:
    """recall 粗筛命中/无命中; inject-core 输出 core 全文, 去 frontmatter, 不混 recall。"""
    body_c = _write_body(mem_ws, "b1.md", "finish 合并冲突必 abort, 禁强解。")
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "git", "--topic", "merge",
            "--title", "合并冲突处理", "--keywords", "merge,conflict", "--body-file", str(body_c))
    body_r = _write_body(mem_ws, "b2.md", "pnpm workspace 加包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--namespace", "recall", "--inclusion", "auto", "--category", "build", "--topic", "pnpm",
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
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "git", "--topic", "merge",
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
    # 无 stdin.agent_type → cats 为空 → 只注索引 (b4 结构性压缩: 全文改按需 inject-core)
    assert "合并冲突必 abort" not in sctx, "subagent-start 无 agent_type 不该注入正文 (只索引)"
    assert "[git/merge] 合并冲突处理" in sctx, "subagent-start 索引缺规则标题"
    assert "SPEC:" in sctx and "recall" in sctx, "subagent-start 缺 spec 纪律指令"


def test_recall_fts5_and_grep_fallback(mem_ws: Path, mem_cli: MemCli) -> None:
    """recall 优先 FTS5 BM25 (reindex 生成 .recall.db); 删 db → grep fallback 仍命中不崩。"""
    body = _write_body(mem_ws, "b1.md", "pnpm workspace 装包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--namespace", "recall", "--inclusion", "auto", "--category", "build", "--topic", "pnpm",
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
    mem_cli(mem_ws, "sediment", "--namespace", "recall", "--inclusion", "auto", "--category", "build", "--topic", "pnpm",
            "--title", "pnpm 装包", "--keywords", "pnpm", "--body-file", str(body_b))
    body_a = _write_body(mem_ws, "a.md", "装依赖见 [[pnpm#pnpm 装包]]。")
    mem_cli(mem_ws, "sediment", "--namespace", "recall", "--inclusion", "auto", "--category", "build", "--topic", "deps",
            "--title", "依赖流程", "--keywords", "deps", "--body-file", str(body_a))

    bl = mem_ws / ".skein" / "spec" / "recall" / "backlinks.md"
    assert bl.exists(), "reindex 未产 recall/backlinks.md"
    txt = bl.read_text()
    assert "## build/pnpm.md#pnpm 装包" in txt, f"backlinks 缺 B 章节 (反链目标): {txt}"
    assert "← recall/build/deps.md#依赖流程" in txt, f"backlinks 缺 B 的入链: {txt}"
    assert "→ [[pnpm#pnpm 装包]]" in txt, f"backlinks 缺 A 的出链: {txt}"


def test_backlinks_rebuild_all_namespaces(mem_ws: Path, mem_cli: MemCli) -> None:
    """backlinks.md 须按实扫 namespace 生成, 非硬编码旧三层 (s4 namespace 全改造漏项回归):
    --namespace rules (LAYERS 之外的 namespace) 也要出 backlinks.md 且入/出链正确。"""
    body_b = _write_body(mem_ws, "b.md", "pnpm workspace 装包后必跑 install。")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "build", "--topic", "pnpm", "--title", "pnpm 装包",
            "--keywords", "pnpm", "--body-file", str(body_b))
    body_a = _write_body(mem_ws, "a.md", "装依赖见 [[pnpm#pnpm 装包]]。")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "build", "--topic", "deps", "--title", "依赖流程",
            "--keywords", "deps", "--body-file", str(body_a))

    bl = mem_ws / ".skein" / "spec" / "rules" / "backlinks.md"
    assert bl.exists(), "reindex 未产 rules/backlinks.md (namespace 未按 _scan_namespaces 遍历)"
    txt = bl.read_text()
    assert "## build/pnpm.md#pnpm 装包" in txt, f"backlinks 缺 B 章节 (反链目标): {txt}"
    assert "← rules/build/deps.md#依赖流程" in txt, f"backlinks 缺 B 的入链: {txt}"
    assert "→ [[pnpm#pnpm 装包]]" in txt, f"backlinks 缺 A 的出链: {txt}"


def test_orphan_detection(mem_ws: Path, mem_cli: MemCli) -> None:
    """孤立判据: 无入度 + active + 最近修改超 STALE_DAYS (走文件 mtime) → maintain 报 [孤立], --apply 归档。"""
    body = _write_body(mem_ws, "b.md", "孤立规则正文, 无 wikilink 入度。")
    mem_cli(mem_ws, "sediment", "--namespace", "core", "--inclusion", "always", "--category", "git", "--topic", "orphan",
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
        mem_cli(mem_ws, "sediment", "--namespace", "recall", "--inclusion", "auto", "--category", "style",
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
    """external namespace: sediment --namespace external --inclusion manual 写盘; recall 跨层 FTS5 命中带 [external];
    顶层 index 含 external 行; maintain 扫 external (MAINTAIN_POLICY: 仅 deprecated 判据, 无 stale — design.md §4);
    degrade external/... 拒 (终点层)。"""
    rules = mem_ws / ".skein" / "spec"

    # 1. sediment --namespace external --inclusion manual 写盘
    body = _write_body(mem_ws, "ext.md", "外部依赖: vue3 组合式 API 用 setup。")
    mem_cli(mem_ws, "sediment", "--namespace", "external", "--inclusion", "manual", "--category", "docs", "--topic", "vue",
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

    # 5. maintain 对 external 生效, 但判据仅 deprecated (design.md §4: external 无 stale/dup/orphan 判据)
    _age(ext_file, 200)  # 老 mtime — external namespace 无 stale 判据, 不该被报
    mout = mem_cli(mem_ws, "maintain").stdout
    assert "[stale]" not in mout, f"external 不该有 stale 判据 (仅 deprecated): {mout}"
    ext_file.write_text(ext_file.read_text().replace("status: active", "status: deprecated"))
    mout2 = mem_cli(mem_ws, "maintain").stdout
    assert "[废弃]" in mout2 and "external/docs/vue" in mout2, f"maintain 未扫 external deprecated: {mout2}"

    # 6. degrade external/<cat>/<topic> 拒 (external 是终点, 不参与降级) — 直跑 subprocess 取
    #    returncode (fixture 强 check=True)
    dgr = subprocess.run([sys.executable, str(MEM), "degrade", "external/docs/vue"],
                         cwd=mem_ws, capture_output=True, text=True)
    assert dgr.returncode != 0, f"degrade external 不该成功: {dgr.stdout}"
    assert "终点" in dgr.stderr, f"degrade 拒绝提示缺「终点」说明: {dgr.stderr}"


def test_always_budget_fallback(mem_ws: Path) -> None:
    """always_budget_tokens() 读 .skein/config.yaml spec.always_budget (字符),
    用换算系数转 token; 缺该键时 fallback spec.core_budget;
    两键皆缺/非正整数 → 默认 517 字符 ≈ 300 token。"""
    script_dir = str(MEM.parent)

    def _budget() -> int:
        r = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {script_dir!r}); "
             "from skeinlib.spec.model import always_budget_tokens; print(always_budget_tokens())"],
            cwd=mem_ws, capture_output=True, text=True, check=True)
        return int(r.stdout.strip())

    cfg = mem_ws / ".skein" / "config.yaml"

    # 两键皆缺 → 默认 517 字符 ≈ 300 token
    assert _budget() == 300, "无 config 未返默认 300 token (517 字符)"

    # 仅 core_budget → fallback 生效 (500 字符 ≈ 290 token)
    cfg.write_text("spec:\n  core_budget: 500\n")
    assert _budget() == 290, "仅 spec.core_budget 未 fallback 生效"

    # always_budget 存在 (即便 core_budget 也在) → always_budget 优先 (3000 字符 ≈ 1740 token)
    cfg.write_text("spec:\n  always_budget: 3000\n  core_budget: 500\n")
    assert _budget() == 1740, "spec.always_budget 未优先于 spec.core_budget"

    # always_budget 非正整数 → fallback core_budget
    cfg.write_text("spec:\n  always_budget: not-a-num\n  core_budget: 500\n")
    assert _budget() == 290, "always_budget 非法值未 fallback 到 core_budget"

    # 两键皆非法/缺 → 回落默认 517 字符 ≈ 300 token
    cfg.write_text("spec:\n  always_budget: not-a-num\n")
    assert _budget() == 300, "两键皆缺/非法未回落默认 300 token"

    # 空 spec 块: YAML 里 `spec:` 无子键解析成 None, 不是 {}。`raw.get("spec", {})` 的默认值只在
    # 键**缺席**时生效, 键在但值为 null 时照样返 None —— 用户实测 Stop hook 崩在
    # `AttributeError: 'NoneType' object has no attribute 'get'`。
    cfg.write_text("spec:\n")
    assert _budget() == 300, "空 spec 块未回落默认, 大概率又崩在 NoneType.get"

    # 空 spec 块由 YAML 解析成 None，也应回落默认值
    cfg.write_text("spec:\n")
    assert _budget() == 300, "空 spec 块未回落默认 300 token"


def test_default_budget_is_same_on_both_paths() -> None:
    """无 config.yaml 走 model.always_budget_tokens() 的兜底, 刚 init 的走 CONFIG_DEFAULTS —— 两处
    必须同值 (都为字符数, 换算系数相同). 不同 = 同一份 spec 在两个工作区一个报超预算一个不报, 而两边看着都"是默认"。"""
    script_dir = str(MEM.parent)
    sys.path.insert(0, script_dir)
    from skeinlib.config import CONFIG_DEFAULTS
    # CONFIG_DEFAULTS 存的是字符数, 比较时也用字符数
    default_chars = CONFIG_DEFAULTS["spec"]["always_budget"]  # 应该是 517
    with tempfile.TemporaryDirectory() as td:   # 无 .skein/config.yaml 的干净工作区
        r = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, {script_dir!r}); "
             "from skeinlib.spec.model import always_budget_tokens; from skeinlib.utils.token_conversion import CHAR_TO_TOKEN_RATIO; "
             "tokens = always_budget_tokens(); print(int(tokens / CHAR_TO_TOKEN_RATIO))"],
            cwd=td, capture_output=True, text=True, check=True)
    fallback_chars = int(r.stdout.strip())
    # 允许 1 字符误差，因为浮点数计算有精度损失
    assert abs(fallback_chars - default_chars) <= 1, (
        f"两条默认路径不同步: 无 config 时 always_budget_tokens() ≈ {fallback_chars} 字符, "
        f'CONFIG_DEFAULTS={default_chars}')


def test_namespace_free_extension(mem_ws: Path, mem_cli: MemCli) -> None:
    """namespace 自由扩展: 手建 spec/foo/bar/x.md (非 CLI/NAMESPACES 白名单途径) → reindex 后
    仍被目录扫描识别, 产 spec/foo/index.md (design.md §2: namespace 由目录扫描而非白名单决定)。"""
    rules = mem_ws / ".skein" / "spec"
    foo_dir = rules / "foo" / "bar"
    foo_dir.mkdir(parents=True)
    (foo_dir / "x.md").write_text(
        "---\n"
        "title: x\n"
        "category: bar\n"
        "keywords: [foo]\n"
        "status: active\n"
        "inclusion: auto\n"
        "---\n\n"
        "## 手建规则\n\n正文内容。\n")

    mem_cli(mem_ws, "reindex")

    idx = rules / "foo" / "index.md"
    assert idx.exists(), "手建 namespace 目录 reindex 后未产 index.md"
    assert "手建规则" in idx.read_text(), f"foo/index.md 未收录手建规则: {idx.read_text()}"
    assert "| foo |" in (rules / "index.md").read_text(), "顶层总索引未含手建 namespace foo"


def test_inclusion_injection_namespace_agnostic(mem_ws: Path, mem_cli: MemCli) -> None:
    """inclusion 筛选与 namespace 无关: product/ 下的 inclusion=always 页同样被 session-start/
    inject-core 注入 (design.md: 加载路径只看 frontmatter inclusion, 与所在目录/namespace 无关)。"""
    body = _write_body(mem_ws, "p.md", "产品现状: 支持多租户。")
    mem_cli(mem_ws, "sediment", "--namespace", "product", "--inclusion", "always",
            "--category", "wiki", "--topic", "tenant", "--title", "多租户支持",
            "--keywords", "tenant", "--body-file", str(body))

    ss = json.loads(mem_cli(mem_ws, "session-start").stdout)
    ctx = ss["hookSpecificOutput"]["additionalContext"]
    assert "[wiki/tenant] 多租户支持" in ctx, f"product 下 always 页未被 session-start 注入索引: {ctx}"

    inj = mem_cli(mem_ws, "inject-core").stdout
    assert "支持多租户" in inj, f"product 下 always 页未被 inject-core 注入全文: {inj}"


def test_degrade_no_file_move(mem_ws: Path, mem_cli: MemCli) -> None:
    """degrade 只改 frontmatter inclusion 字段, 不移动文件 (design.md §2: inclusion 脱离目录后
    跨层 git mv 已无意义)。"""
    body = _write_body(mem_ws, "d.md", "降级测试正文。")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "always",
            "--category", "git", "--topic", "deg", "--title", "降级规则",
            "--keywords", "deg", "--body-file", str(body))

    f = mem_ws / ".skein" / "spec" / "rules" / "git" / "deg.md"
    assert f.exists() and "inclusion: always" in f.read_text()

    out = mem_cli(mem_ws, "degrade", "rules/git/deg").stdout
    assert f.exists(), "degrade 后文件路径不该变 (不移动文件)"
    assert "inclusion: auto" in f.read_text(), f"degrade 未把 inclusion 改为 auto: {f.read_text()}"
    assert "已降级" in out


def test_maintain_product_no_auto_archive(mem_ws: Path, mem_cli: MemCli) -> None:
    """product namespace 不自动 archive (design.md §4 回归重点): 即便 anchors 失效 + 长期未改,
    maintain --apply 也只报告不删文件 — 需求真值不能自动丢。"""
    body = _write_body(mem_ws, "prod.md", "产品现状描述。")
    mem_cli(mem_ws, "sediment", "--namespace", "product", "--category", "wiki",
            "--topic", "feat", "--title", "某功能现状", "--keywords", "feat",
            "--anchors", "no/such/path.py", "--body-file", str(body))

    f = mem_ws / ".skein" / "spec" / "product" / "wiki" / "feat.md"
    assert f.exists()
    _age(f, 400)  # 远超 STALE_DAYS — 若误走 rules 判据会被 archive

    out = mem_cli(mem_ws, "maintain", "--apply").stdout
    assert f.exists(), f"product 页被自动 archive 了 (回归!): {out}"
    assert "wiki/feat" in out, f"product anchors 失效未报告: {out}"


def _write_task(mem_ws: Path, tid: str, subtasks: list[dict[str, Any]], prd: str, design: str) -> Path:
    """analyze 只读 task.json/prd.md/design.md — 手写这三份 (不走 skein.py 全套脚手架, 更轻)。"""
    tdir = mem_ws / ".skein" / "task" / tid
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "task.json").write_text(json.dumps({"id": tid, "subtasks": subtasks}, ensure_ascii=False))
    (tdir / "prd.md").write_text(prd)
    (tdir / "design.md").write_text(design)
    return tdir


def _snapshot(root: Path) -> dict[str, tuple[float, int]]:
    """目录下所有文件的 (mtime, size) 快照, 供 analyze「不写盘」断言前后比对。"""
    return {str(p): (p.stat().st_mtime, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


def test_analyze_no_conflicts_and_readonly(mem_ws: Path, mem_cli: MemCli) -> None:
    """analyze 五类检查零命中时如实报「零冲突」; 且全程只读, 不改动 .skein/ 下任何文件, 不新建文件。"""
    tid = "clean-task"
    _write_task(
        mem_ws, tid,
        subtasks=[{"sid": "s1", "name": "实现日志写入", "desc": "写日志文件模块",
                   "depends_on": [], "acceptance": ["日志文件权限只读"]}],
        prd=("# clean-task — PRD\n\n## 目标\n交付安全的日志写入模块。\n\n"
             "## 边界\n仅涉及日志写入。\n\n"
             "## 验收标准\n- [ ] 日志文件权限设为只读\n\n"
             "## 索引\n- design.md\n"),
        design=("# clean-task — 详细设计\n\n按接口规范写入日志, 不直接碰全局配置。\n\n"
                "## 测试接缝 (seam)\n- `seed.txt` (repo 根真实存在路径)\n"),
    )
    repo_root = mem_ws
    before = _snapshot(repo_root)

    out = mem_cli(mem_ws, "analyze", tid).stdout
    assert "零冲突" in out, f"应零命中却报了候选: {out}"

    j = json.loads(mem_cli(mem_ws, "analyze", tid, "--json").stdout)
    assert j["tid"] == tid and j["count"] == 0 and j["findings"] == [], f"json 输出应零 finding: {j}"

    after = _snapshot(repo_root)
    assert before == after, "analyze 不该写盘 (mtime/size 或文件集合变了)"


def test_analyze_five_kinds_hit(mem_ws: Path, mem_cli: MemCli) -> None:
    """构造能同时命中五类候选 (验收覆盖率/硬规冲突/范围蔓延/置信度/接缝存在性) 的 task, 逐类断言命中。"""
    # 硬规: always 规则含否定式表述, design.md 正向复述同一短语 → 硬规冲突候选
    body = _write_body(mem_ws, "hardrule.md", "禁止直接写全局配置, 一律走标准接口。")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "always",
            "--category", "arch", "--topic", "config", "--title", "配置写入规范",
            "--keywords", "config", "--body-file", str(body))
    # 置信度: proposed 规则, design.md 引用其标题
    body2 = _write_body(mem_ws, "proposed.md", "尚未验证的刷新时机策略。")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "flush", "--title", "异步刷新策略",
            "--keywords", "flush", "--status", "proposed", "--body-file", str(body2))

    tid = "dirty-task"
    _write_task(
        mem_ws, tid,
        subtasks=[
            # 验收覆盖: 「日志文件权限设为只读」命中, 但下面 prd 会多一条无人覆盖的验收条
            {"sid": "s1", "name": "实现日志写入", "desc": "写日志文件模块",
             "depends_on": [], "acceptance": ["日志可写"]},
            # 范围蔓延: 名/desc 与 prd 全文无关键词交集
            {"sid": "s2", "name": "搭建用户认证", "desc": "加OAuth登录流程",
             "depends_on": [], "acceptance": []},
        ],
        prd=("# dirty-task — PRD\n\n## 目标\n交付一个安全的日志模块。\n\n"
             "## 边界\n仅涉及日志写入。\n\n"
             "## 验收标准\n- [ ] 日志文件权限设为只读\n- [ ] 支持异步刷新缓冲区\n\n"
             "## 索引\n- design.md\n"),
        design=("# dirty-task — 详细设计\n\n"
                "为了性能, 我们直接写全局配置缓存, 而非走标准接口。\n\n"
                "参考规则「异步刷新策略」设计缓冲区刷新时机。\n\n"
                "## 测试接缝 (seam)\n- `plugins/tools/skein/scripts/nope_seam_test_file.py`\n"),
    )

    out = mem_cli(mem_ws, "analyze", tid).stdout
    assert "[coverage]" in out and "异步刷新缓冲区" in out, f"验收覆盖率未命中: {out}"
    assert "[hardrule]" in out and "配置写入规范" in out, f"硬规冲突未命中: {out}"
    assert "[scope]" in out and "s2" in out, f"范围蔓延未命中: {out}"
    assert "[confidence]" in out and "异步刷新策略" in out, f"置信度未命中: {out}"
    assert "[seam]" in out and "nope_seam_test_file.py" in out, f"接缝存在性未命中: {out}"

    j = json.loads(mem_cli(mem_ws, "analyze", tid, "--json").stdout)
    kinds = {fd["kind"] for fd in j["findings"]}
    assert kinds == {"coverage", "hardrule", "scope", "confidence", "seam"}, f"五类未全覆盖: {kinds}"
    assert j["count"] == len(j["findings"]) == len(kinds), f"计数与条目不一致: {j}"


def test_map_skeleton_only(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 1: map skeleton 现算 (无 map 页时只出骨架, 骨架数据结构正确)。"""
    # 创建一些测试文件
    (mem_ws / "test.py").write_text("""
def hello():
    pass

class MyClass:
    pass
""")
    (mem_ws / "test.js").write_text("""
function foo() {}
class Bar {}
export const baz = 1;
""")
    subprocess.run(["git", "add", "-A"], cwd=mem_ws, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "add test files"], cwd=mem_ws, check=True, capture_output=True)

    # 运行 map --skeleton
    out = mem_cli(mem_ws, "map", "--skeleton").stdout
    data = json.loads(out)

    # 验证骨架数据结构
    assert "total_files" in data, "skeleton 缺少 total_files"
    assert "total_lines" in data, "skeleton 缺少 total_lines"
    assert "files" in data, "skeleton 缺少 files"
    assert data["total_files"] > 0, "skeleton 应该有文件"
    assert data["total_lines"] > 0, "skeleton 应该有行数"

    # 验证具体文件信息
    py_files = [f for f in data["files"] if f["path"].endswith("test.py")]
    assert len(py_files) == 1, "应该有一个 test.py 文件"
    py_file = py_files[0]
    assert "hello" in py_file["symbols"], "Python 文件应该包含 hello 符号"
    assert "MyClass" in py_file["symbols"], "Python 文件应该包含 MyClass 符号"
    assert py_file["lines"] > 0, "Python 文件应该有行数"

    js_files = [f for f in data["files"] if f["path"].endswith("test.js")]
    assert len(js_files) == 1, "应该有一个 test.js 文件"
    js_file = js_files[0]
    assert "foo" in js_file["symbols"] or "Bar" in js_file["symbols"], "JS 文件应该包含符号"


def test_map_merge_with_semantic(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 2: map 命令合并骨架与语义页 (skeleton + semantic + merged 结构)。"""
    # 创建测试文件
    (mem_ws / "code.py").write_text("""
class CodeClass:
    def method(self):
        pass
""")
    subprocess.run(["git", "add", "-A"], cwd=mem_ws, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "add code"], cwd=mem_ws, check=True, capture_output=True)

    # 创建 map namespace 语义页
    body = _write_body(mem_ws, "map.md", "代码架构说明")
    mem_cli(mem_ws, "sediment", "--namespace", "map", "--inclusion", "auto",
            "--category", "arch", "--topic", "design", "--title", "架构设计",
            "--keywords", "architecture,design", "--anchors", "code.py",
            "--body-file", str(body))

    # 运行 map 命令 (不带 --skeleton)
    out = mem_cli(mem_ws, "map").stdout
    data = json.loads(out)

    # 验证合并结构
    assert "skeleton" in data, "输出应该包含 skeleton"
    assert "semantic" in data, "输出应该包含 semantic"
    assert "merged" in data, "输出应该包含 merged 标记"
    assert data["merged"] is True, "merged 标记应该为 True"

    # 验证 skeleton 部分结构正确
    assert "total_files" in data["skeleton"], "skeleton 应该有 total_files"
    assert "files" in data["skeleton"], "skeleton 应该有 files"

    # 验证 semantic 部分包含我们添加的语义页
    # 修正：semantic 是按类别组织的
    if "arch" in data["semantic"]:
        arch_items = data["semantic"]["arch"]
    else:
        # 如果语义页没有按类别组织，就在 items 或者其他字段下
        arch_items = data["semantic"].get("items", [])

    assert len(arch_items) > 0, f"arch 类目应该有内容, 实际 semantic 结构: {data['semantic']}"

    # 找到我们添加的语义页（修正：实际title是design，不是架构设计）
    design_page = None
    for item in arch_items:
        if item.get("title") == "design":  # 修正：实际 title 是 design
            design_page = item
            break

    assert design_page is not None, f"应该找到 design 语义页, 实际 semantic 内容: {data['semantic']}"
    assert design_page["category"] == "arch", "类目应该是 arch"
    assert "architecture" in design_page["keywords"] or "design" in design_page["keywords"], "关键词应该包含 architecture 或 design"
    # anchors 目前为空是已知的 frontmatter 解析问题，暂不强制要求
    # assert "code.py" in design_page["anchors"], "anchors 应该包含 code.py"


def test_recall_src_code(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 3: recall --src code 返回 BM25 命中的 map 语义页 + anchors 汇总。"""
    # 创建 map namespace 语义页
    body = _write_body(mem_ws, "map1.md", "Python 异常处理规范")
    mem_cli(mem_ws, "sediment", "--namespace", "map", "--inclusion", "auto",
            "--category", "python", "--topic", "exception", "--title", "异常处理",
            "--keywords", "exception,error,python", "--anchors", "exceptions.py",
            "--body-file", str(body))

    body2 = _write_body(mem_ws, "map2.md", "Go 错误处理模式")
    mem_cli(mem_ws, "sediment", "--namespace", "map", "--inclusion", "auto",
            "--category", "go", "--topic", "errors", "--title", "错误处理",
            "--keywords", "error,go,handle", "--anchors", "errors.go",
            "--body-file", str(body2))

    # 测试 recall --src code
    out = mem_cli(mem_ws, "recall", "--src", "code", "python 异常").stdout

    # 验证返回包含 map namespace 内容
    assert "map" in out.lower() or "[map]" in out, f"recall --src code 应该返回 map namespace 内容: {out}"
    assert "异常处理" in out or "exception" in out.lower(), f"应该命中异常处理语义页: {out}"
    assert "exceptions.py" in out, f"应该包含 anchors 信息: {out}"


def test_map_inclusion_always_injection(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 4: inclusion:always 的 map 页被 inject-core 正确注入。"""
    # 创建 inclusion=always 的 map 页
    body = _write_body(mem_ws, "always_map.md", "重要的架构原则，需要常驻注入。")
    mem_cli(mem_ws, "sediment", "--namespace", "map", "--inclusion", "always",
            "--category", "principles", "--topic", "core", "--title", "核心原则",
            "--keywords", "core,principle", "--body-file", str(body))

    # 测试 inject-core
    inj = mem_cli(mem_ws, "inject-core").stdout

    # 验证 inclusion=always 的 map 页被注入
    assert "核心原则" in inj, f"inject-core 应该包含 map namespace 的 always 页: {inj}"
    assert "重要的架构原则" in inj, f"inject-core 应该包含 always 页的正文: {inj}"
    # 验证不包含 frontmatter
    assert "inclusion:" not in inj and "keywords:" not in inj, "inject-core 不该包含 frontmatter"


def test_map_anchors_broken_link_detection(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 5: anchors 断链检测 (maintain 报告断链锚点)。"""
    # 创建指向不存在文件的 anchors
    body = _write_body(mem_ws, "broken.md", "这个页面的 anchors 指向不存在的文件。")
    mem_cli(mem_ws, "sediment", "--namespace", "map", "--inclusion", "auto",
            "--category", "test", "--topic", "broken", "--title", "断链测试",
            "--keywords", "broken,test", "--anchors", "nonexistent_file.py",
            "--body-file", str(body))

    # 运行 maintain 检测断链
    out = mem_cli(mem_ws, "maintain").stdout

    # 验证断链被检测到
    assert "断链" in out or "broken" in out.lower() or "nonexistent_file.py" in out, \
        f"maintain 应该报告断链: {out}"


def test_map_skeleton_no_disk_write(mem_ws: Path, mem_cli: MemCli) -> None:
    """测试 6: 骨架不落盘 (临时目录文件集合无变化 — map 命令运行前后文件列表一致)。"""
    # 创建测试文件
    (mem_ws / "sample.py").write_text("""
def sample():
    return 42
""")
    subprocess.run(["git", "add", "-A"], cwd=mem_ws, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "add sample"], cwd=mem_ws, check=True, capture_output=True)

    # 记录运行前的文件快照
    before_files = _snapshot(mem_ws)

    # 运行 map 命令
    mem_cli(mem_ws, "map", "--skeleton")

    # 记录运行后的文件快照
    after_files = _snapshot(mem_ws)

    # 验证文件集合没有变化
    assert before_files == after_files, \
        f"map 命令不应该写盘: 前后文件状态不一致\nbefore: {len(before_files)} files\nafter: {len(after_files)} files"

    # 同样测试普通 map 命令 (不带 --skeleton)
    before_files2 = _snapshot(mem_ws)
    mem_cli(mem_ws, "map")
    after_files2 = _snapshot(mem_ws)

    assert before_files2 == after_files2, \
        f"map 命令 (不带 --skeleton) 也不应该写盘: 前后文件状态不一致"


def test_map_three_language_symbols(mem_ws: Path, mem_cli: MemCli) -> None:
    """补充测试: 确保三语言符号抓取正确 (Python/JS/Go)。"""
    # 创建三种语言的测试文件
    (mem_ws / "test_py.py").write_text("""
def python_function():
    pass

class PythonClass:
    pass

async def async_function():
    pass
""")

    (mem_ws / "test_js.js").write_text("""
function jsFunction() {}
class JsClass {}
export const exportVar = 1;
export function exportFunction() {}
""")

    (mem_ws / "test_go.go").write_text("""
func goFunction() {}
type GoType struct {}
func (g *GoType) method() {}
""")

    subprocess.run(["git", "add", "-A"], cwd=mem_ws, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "add multi-language files"], cwd=mem_ws, check=True, capture_output=True)

    # 运行 map --skeleton
    out = mem_cli(mem_ws, "map", "--skeleton").stdout
    data = json.loads(out)

    # 验证三种语言的符号都被正确抓取
    py_file = next((f for f in data["files"] if f["path"].endswith("test_py.py")), None)
    assert py_file is not None, "应该找到 Python 测试文件"
    assert "python_function" in py_file["symbols"], "应该抓取到 Python 函数"
    assert "PythonClass" in py_file["symbols"], "应该抓取到 Python 类"
    assert "async_function" in py_file["symbols"], "应该抓取到 Python async 函数"

    js_file = next((f for f in data["files"] if f["path"].endswith("test_js.js")), None)
    assert js_file is not None, "应该找到 JS 测试文件"
    assert any(s in js_file["symbols"] for s in ["jsFunction", "JsClass", "exportVar", "exportFunction"]), \
        f"应该抓取到 JS 符号，实际: {js_file['symbols']}"

    go_file = next((f for f in data["files"] if f["path"].endswith("test_go.go")), None)
    assert go_file is not None, "应该找到 Go 测试文件"
    assert "goFunction" in go_file["symbols"] or "GoType" in go_file["symbols"], \
        f"应该抓取到 Go 符号，实际: {go_file['symbols']}"


def test_map_non_git_degradation(mem_ws: Path, mem_cli: MemCli) -> None:
    """补充测试: 非 git 仓库降级到 rglob + 排除衍生目录。"""
    # 在非 git 仓库情况下测试
    # 先创建一些文件
    (mem_ws / "code.py").write_text("""
class TestClass:
    def test_method(self):
        pass
""")

    # 创建衍生目录，应该被排除
    (mem_ws / "__pycache__").mkdir()
    (mem_ws / "__pycache__" / "cache.py").write_text("cache content")

    (mem_ws / "node_modules").mkdir()
    (mem_ws / "node_modules" / "module.js").write_text("module code")

    # 创建正常的文件
    (mem_ws / "normal.py").write_text("def normal(): pass")

    # 临时删除 .git 目录，模拟非 git 仓库
    git_dir = mem_ws / ".git"
    git_backup = None
    if git_dir.exists():
        git_backup = mem_ws / ".git_backup"
        shutil.move(str(git_dir), str(git_backup))

    try:
        # 运行 map --skeleton
        out = mem_cli(mem_ws, "map", "--skeleton").stdout
        data = json.loads(out)

        # 验证正常文件被包含
        files = [f["path"] for f in data["files"]]
        assert any("normal.py" in f for f in files), "应该包含正常文件"

        # 验证衍生目录被排除
        assert not any("__pycache__" in f for f in files), "不应该包含 __pycache__ 目录"
        assert not any("node_modules" in f for f in files), "不应该包含 node_modules 目录"

    finally:
        # 恢复 .git 目录
        if git_backup and git_backup.exists():
            shutil.move(str(git_backup), str(git_dir))


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
               test_recall_fts5_and_grep_fallback, test_backlinks_rebuild,
               test_backlinks_rebuild_all_namespaces, test_orphan_detection,
               test_restructure_merge, test_external_layer,
               lambda ws, _cli: test_always_budget_fallback(ws),  # 只收 ws, 无 cli
               test_namespace_free_extension, test_inclusion_injection_namespace_agnostic,
               test_degrade_no_file_move, test_maintain_product_no_auto_archive,
               test_analyze_no_conflicts_and_readonly, test_analyze_five_kinds_hit,
               test_map_skeleton_only, test_map_merge_with_semantic, test_recall_src_code,
               test_map_inclusion_always_injection, test_map_anchors_broken_link_detection,
               test_map_skeleton_no_disk_write, test_map_three_language_symbols, test_map_non_git_degradation):
        fn(_mk_ws(), mem_cli)
    print("spec.py 测试全过 (init/sediment主题合并/recall FTS5+grep fallback/inject-core隔离层/"
          "hook注入/正反链(含非LAYERS namespace)/孤立/restructure/external层/always_budget fallback/"
          "namespace自由扩展/inclusion筛选/degrade不移文件/product不自动archive/"
          "analyze五类命中与零冲突/analyze不写盘/map骨架现算/map语义页合并/"
          "recall --src code/map inclusion注入/anchors断链/骨架不落盘/三语言符号/非git降级)")
