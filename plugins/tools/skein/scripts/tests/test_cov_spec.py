"""spec 层补覆盖 — 进程内单测 (直接 import Spec, 不走 subprocess)。

钉的是各 mixin 的**降级/容错/边界分支**: frontmatter 流式数组解析、预算 null 边界、
FTS 不可用降级 grep、anchors 强/弱断链、archive/restore 可逆性、amend 章节改写。
主流程 (sediment/reindex/recall 正路) 已由 test_spec.py 覆盖, 本文件只补它没走到的岔路。
"""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from skeinlib.spec.facade import Spec
from skeinlib.spec import model as spec_model
from skeinlib.spec.text import _frontmatter, _link_target


def _spec(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Spec:
    """在隔离仓内造 Spec 实例 — Spec.__init__ 走 spec_root() 读 cwd, 必须先 chdir。"""
    monkeypatch.chdir(ws)
    return Spec()


def _write_rule(ws: Path, ns: str, cat: str, topic: str, fm: str, body: str) -> Path:
    """直接落一个规则文件 (绕开 sediment, 便于构造非法/特殊 frontmatter)。"""
    d = ws / ".skein" / "spec" / ns / cat
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{topic}.md"
    f.write_text(f"---\n{fm}---\n\n{body}\n")
    return f


# ══════════════════════ text.py ══════════════════════

def test_link_target_strips_md_suffix() -> None:
    """带 .md 后缀与目录前缀的 wikilink 归一成 `stem#锚点` — 反链表靠这个键对齐。"""
    assert _link_target("rules/git/merge.md#冲突处理") == "merge#冲突处理"
    assert _link_target("rules/git/merge.md") == "merge"


def test_frontmatter_missing_or_unterminated_returns_empty() -> None:
    """无 frontmatter / 只有开头 `---` 没有结尾 → 空 dict, 不抛 (容错优先, 免一篇坏规则炸整次注入)。"""
    assert _frontmatter("# 纯正文\n") == {}
    assert _frontmatter("---\ntitle: x\nkeywords: [a]\n") == {}


def test_frontmatter_flow_array_flushed_by_next_key() -> None:
    """流式数组 (多行 `- item`) 在遇到下一个顶层键时落袋, 转成逗号分隔串。"""
    meta = _frontmatter("---\nkeywords:\n  - alpha\n  - beta\nstatus: active\n---\n\nbody\n")
    assert meta["keywords"] == "alpha, beta"
    assert meta["status"] == "active"


def test_frontmatter_flow_array_at_tail_flushed_at_end() -> None:
    """流式数组是最后一个键时, 靠循环结束后的兜底 flush 落袋 (否则整组丢失)。"""
    meta = _frontmatter("---\ntitle: t\nanchors:\n  - a/b.py\n  - c/d.py\n---\n\nbody\n")
    assert meta["anchors"] == "a/b.py, c/d.py"


# ══════════════════════ model.py ══════════════════════

def test_read_hook_stdin_parses_agent_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """hook stdin 是合法 JSON → 取出 agent_type (SubagentStart 按 agent 分类目注入靠它)。"""
    monkeypatch.setattr("sys.stdin", io.StringIO('{"agent_type": "skein-executor"}'))
    assert spec_model._read_hook_stdin() == "skein-executor"


def test_read_hook_stdin_bad_json_falls_back_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin 非 JSON → None 而非抛异常 (hook 不能因为脏输入炸掉整次会话启动)。"""
    monkeypatch.setattr("sys.stdin", io.StringIO("not-a-json"))
    assert spec_model._read_hook_stdin() is None


def test_read_hook_stdin_json_array_falls_back_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin 是 JSON 数组 → .get 触发 AttributeError, 同样降级 None。"""
    monkeypatch.setattr("sys.stdin", io.StringIO("[1, 2]"))
    assert spec_model._read_hook_stdin() is None


def test_spec_root_without_git_binary_falls_back_to_cwd(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """无 git 二进制 → 退回 cwd/.skein/spec (设计意图: 非 git 仓也能用)。"""
    def _boom(*_a: object, **_k: object) -> object:
        raise FileNotFoundError("git not found")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("skeinlib.spec.model.subprocess.run", _boom)
    assert spec_model.spec_root() == tmp_path / ".skein" / "spec"


def test_validate_budget_rejects_non_positive() -> None:
    """预算守卫: 0 / 负数直接抛, 免下游 budget_guard 把注入全截没。"""
    with pytest.raises(ValueError, match="预算必须为正数"):
        spec_model._validate_budget(0)


def test_always_budget_null_spec_block_uses_default(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config.yaml 写成空 `spec:` 块 → YAML 解析成 None, 必须回退默认 517 字符预算。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / ".skein" / "config.yaml").write_text("spec:\n")
    assert spec_model.always_budget_tokens() == 300


def test_always_budget_broken_yaml_uses_default(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config.yaml 语法坏掉 → 吞异常走默认, 不让一处坏配置阻断所有注入。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / ".skein" / "config.yaml").write_text("spec: [unclosed\n")
    assert spec_model.always_budget_tokens() == 300


def test_always_budget_sub_char_values_fall_through_to_default(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """always_budget/core_budget 小到换算后 token=0 → 两级校验都拒, 最终落默认 300。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / ".skein" / "config.yaml").write_text("spec:\n  always_budget: 0.5\n  core_budget: 0.5\n")
    assert spec_model.always_budget_tokens() == 300


def test_always_budget_core_budget_fallback(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """always_budget 缺失 → 回退旧字段 core_budget (字符) 换算。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / ".skein" / "config.yaml").write_text("spec:\n  core_budget: 1000\n")
    assert spec_model.always_budget_tokens() == 580


# ══════════════════════ inject.py ══════════════════════

def _always_rule(ws: Path, cat: str, topic: str, title: str, body: str) -> Path:
    """落一个 inclusion=always 的规则 (常驻注入用)。"""
    return _write_rule(ws, "rules", cat, topic,
                       f"title: {topic}\ncategory: {cat}\nkeywords: []\n"
                       f"status: active\ninclusion: always\n",
                       f"## {title}\n\n{body}")


def test_session_start_silent_when_no_always_rules(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """空库 (无 always 页) → SessionStart 一个字都不注入, 免每轮白付 token。"""
    _spec(mem_ws, monkeypatch).session_start(argparse.Namespace())
    assert capsys.readouterr().out == ""


def test_session_start_appends_maintain_hint_when_over_budget(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """always 页超预算 → 注入尾部追加一行 maintain 提醒 (不挤 session_index 预算)。"""
    _always_rule(mem_ws, "script", "big", "巨型规则", "内容" * 600)
    _spec(mem_ws, monkeypatch).session_start(argparse.Namespace())
    ctx = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
    assert "skein-spec maintain" in ctx


def test_subagent_start_silent_outside_skein_repo(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """非 SKEIN 项目 (无 .skein/spec) → SubagentStart 静默, 免污染其他插件的 agent。"""
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    _spec(tmp_path, monkeypatch).subagent_start(argparse.Namespace())
    assert capsys.readouterr().out == ""


def test_subagent_start_silent_when_index_empty(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """库存在但无 always 页 → 索引为空, 同样不注入。"""
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    _spec(mem_ws, monkeypatch).subagent_start(argparse.Namespace())
    assert capsys.readouterr().out == ""


def test_subagent_start_injects_matched_category_fulltext(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """agent_type 命中 AGENT_CATEGORIES → 该类目注全文, 未命中类目仅进索引。"""
    _always_rule(mem_ws, "script", "hit", "命中规则", "命中类目正文XYZ")
    _always_rule(mem_ws, "arch", "miss", "未命中规则", "未命中类目正文ABC")
    monkeypatch.setattr("sys.stdin", io.StringIO('{"agent_type": "skein-executor"}'))
    _spec(mem_ws, monkeypatch).subagent_start(argparse.Namespace())
    ctx = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
    assert "命中类目正文XYZ" in ctx
    assert "未命中类目正文ABC" not in ctx
    assert "[arch/miss] 未命中规则" in ctx  # 未命中类目仍在索引里


# ══════════════════════ analyze.py ══════════════════════

def _task(ws: Path, tid: str, *, task_json: object = None,
          prd: str = "", design: str = "") -> Path:
    """在 .skein/task/<tid>/ 造 analyze 的输入工件。"""
    d = ws / ".skein" / "task" / tid
    d.mkdir(parents=True, exist_ok=True)
    if task_json is not None:
        (d / "task.json").write_text(json.dumps(task_json, ensure_ascii=False))
    if prd:
        (d / "prd.md").write_text(prd)
    if design:
        (d / "design.md").write_text(design)
    return d


def test_analyze_missing_task_raises(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """task 目录不存在 → 报错并给出查找路径, 不静默产空报告。"""
    from skeinlib.utils.errors import SkeinError
    with pytest.raises(SkeinError, match="task 不存在"):
        _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-nope", json=False))


def test_analyze_zero_findings_reports_clean(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """prd 无验收标准段 / 无 design → 五类判据全跳过, 如实报零冲突而非硬凑。"""
    _task(mem_ws, "t-clean", task_json={"subtasks": []}, prd="# 标题\n\n## 背景\n\n随便写点\n")
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-clean", json=False))
    assert "零冲突" in capsys.readouterr().out


def test_analyze_coverage_and_scope_findings_json(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """验收条在 subtask 无关键词对应 → coverage 候选; subtask 在 prd 无对应 → scope 候选。"""
    prd = ("---\ndesc: zebra 模块交付\nboundary:\n  should: []\n  should_not: []\n"
           "acceptance:\n  - zebra 必须可用\n---\n\n## 其他\n\n收尾\n")
    _task(mem_ws, "t-cov", prd=prd,
          task_json={"subtasks": [{"sid": "s1", "name": "quokka", "desc": "quokka 相关"}]})
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-cov", json=True))
    out = json.loads(capsys.readouterr().out)
    kinds = {f["kind"] for f in out["findings"]}
    assert "coverage" in kinds and "scope" in kinds


def test_analyze_hardrule_skips_same_direction_and_short_phrase(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """design 本身也是否定表述 → 与硬规同向不算冲突; 短语 strip 后 <2 字 → 直接跳过。"""
    _always_rule(mem_ws, "script", "hard", "硬规",
                 "禁止 直接提交主干\n禁止a \n")
    _spec(mem_ws, monkeypatch)._reindex_all()
    _task(mem_ws, "t-hard", task_json={}, design="## 方案\n\n本方案禁止 直接提交主干\n")
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-hard", json=True))
    out = json.loads(capsys.readouterr().out)
    assert [f for f in out["findings"] if f["kind"] == "hardrule"] == []


def test_analyze_hardrule_flags_opposite_direction(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """design 正面写了硬规禁止的短语 → 报 hardrule 候选 (措辞带「需人判」, 不断言违规)。"""
    _always_rule(mem_ws, "script", "hard", "硬规", "禁止 直接提交主干\n")
    _task(mem_ws, "t-hard2", task_json={}, design="## 方案\n\n我们会 直接提交主干 走捷径\n")
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-hard2", json=True))
    out = json.loads(capsys.readouterr().out)
    hits = [f for f in out["findings"] if f["kind"] == "hardrule"]
    assert hits and "需人判" in hits[0]["text"]


def test_analyze_confidence_flags_proposed_rule(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """design 引用了 status=proposed 的规则 → 报未验证引用。"""
    _write_rule(mem_ws, "rules", "arch", "prop",
                "title: prop\ncategory: arch\nkeywords: []\nstatus: proposed\ninclusion: auto\n",
                "## 待验证决策\n\n正文\n")
    _task(mem_ws, "t-conf", task_json={}, design="## 方案\n\n依据 待验证决策 展开\n")
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-conf", json=True))
    out = json.loads(capsys.readouterr().out)
    assert any(f["kind"] == "confidence" for f in out["findings"])


def test_analyze_seam_reports_missing_path_and_symbol(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """「测试接缝」段声明的路径/符号在 codebase 找不到 → 各报一条 seam 缺失; 重复 token 只报一次。"""
    design = ("## 测试接缝\n\n"
              "- `nowhere/missing.py` 与 `nowhere/missing.py` 重复声明\n"
              "- `zzz_no_such_symbol_zzz`\n"
              "- `` 空 token\n")
    _task(mem_ws, "t-seam", task_json={}, design=design)
    _spec(mem_ws, monkeypatch).analyze(argparse.Namespace(tid="t-seam", json=True))
    seams = [f for f in json.loads(capsys.readouterr().out)["findings"] if f["kind"] == "seam"]
    assert len(seams) == 2
    assert any("未找到该路径" in f["text"] for f in seams)
    assert any("git grep 无命中" in f["text"] for f in seams)


def test_analyze_seam_swallows_git_failure(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """无 git 二进制 / git grep 超时 → 跳过该候选, 不因环境问题误报缺失。"""
    def _boom(*_a: object, **_k: object) -> object:
        raise OSError("no git")

    _task(mem_ws, "t-seam2", task_json={}, design="## 测试接缝\n\n- `zzz_no_such_symbol_zzz`\n")
    m = _spec(mem_ws, monkeypatch)
    monkeypatch.setattr("skeinlib.spec.analyze.subprocess.run", _boom)
    m.analyze(argparse.Namespace(tid="t-seam2", json=True))
    assert json.loads(capsys.readouterr().out)["findings"] == []


# ══════════════════════ index.py ══════════════════════

def _make_unreadable(f: Path) -> None:
    """把文件弄成读不出 (模拟权限/损坏); root 下 chmod 无效则跳过该用例。"""
    f.chmod(0o000)
    try:
        f.read_text()
    except OSError:
        return
    pytest.skip("当前用户可无视文件权限 (root?), 读失败分支无法构造")


def test_recall_src_code_no_hit(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """--src code 在空 map namespace 上 → 如实报无命中。"""
    _spec(mem_ws, monkeypatch).recall(argparse.Namespace(query="zzzz", src="code"))
    assert "recall 无命中" in capsys.readouterr().out


def test_recall_quoted_query_degrades_to_grep(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """查询含双引号会破坏 FTS5 MATCH 语法 → 提前降级 grep, 而非抛异常打断 planning。"""
    m = _spec(mem_ws, monkeypatch)
    _write_rule(mem_ws, "rules", "git", "merge",
                "title: merge\ncategory: git\nkeywords: [rebase]\nstatus: active\ninclusion: auto\n",
                "## 合并策略\n\n用 rebase\n")
    m._reindex_all()
    # 注意: grep fallback 用原始 token 做子串匹配 (不剥引号), 所以纯引号词本身命不中 —
    # 这里靠同查询里的干净词 rebase 命中, 钉的是「降级发生了」而非引号词能匹配。
    m.recall(argparse.Namespace(query='rebase "x', src="all"))
    assert "grep fallback" in capsys.readouterr().out


def test_recall_src_filters_by_namespace(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """--src <ns> 走 FTS 的 namespace 过滤列, 只返回该 namespace 的规则。"""
    m = _spec(mem_ws, monkeypatch)
    _write_rule(mem_ws, "rules", "git", "merge",
                "title: merge\ncategory: git\nkeywords: [zebra]\nstatus: active\ninclusion: auto\n",
                "## 规则库侧\n\nzebra\n")
    _write_rule(mem_ws, "product", "feat", "page",
                "title: page\ncategory: feat\nkeywords: [zebra]\nstatus: active\ninclusion: auto\n",
                "## 产品侧\n\nzebra\n")
    m._reindex_all()
    m.recall(argparse.Namespace(query="zebra", src="product"))
    out = capsys.readouterr().out
    assert "产品侧" in out and "规则库侧" not in out


def test_recall_broken_fts_table_degrades_to_grep(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """.recall.db 在但 rules 表没了 (schema 漂移) → OperationalError 降级 grep, 不炸。"""
    m = _spec(mem_ws, monkeypatch)
    _write_rule(mem_ws, "rules", "git", "merge",
                "title: merge\ncategory: git\nkeywords: [zebra]\nstatus: active\ninclusion: auto\n",
                "## 合并策略\n\nzebra\n")
    m._reindex_all()
    con = sqlite3.connect(m.root / ".recall.db")
    con.execute("DROP TABLE rules")
    con.commit()
    con.close()
    m.recall(argparse.Namespace(query="zebra", src="all"))
    assert "grep fallback" in capsys.readouterr().out


def test_recall_grep_skips_namespace_without_index(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """namespace 目录还没 index.md (未 reindex) → grep 跳过它而非 FileNotFoundError。"""
    m = _spec(mem_ws, monkeypatch)
    m._reindex_all()
    (m.root / "rules" / "index.md").unlink()
    assert m._recall_grep("zebra", "all") == []


def test_rebuild_spec_meta_skips_absent_namespace_dir(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """空库退回 NAMESPACES 默认清单时目录并不存在 → spec_meta 重建跳过, 不抛。"""
    import shutil as _shutil
    m = _spec(mem_ws, monkeypatch)
    m._reindex_all()
    for ns in list(m.root.iterdir()):
        if ns.is_dir() and not ns.name.startswith("."):
            _shutil.rmtree(ns)
    m._rebuild_spec_meta()  # 不抛即通过
    con = sqlite3.connect(m.root / ".recall.db")
    assert con.execute("SELECT count(*) FROM spec_meta").fetchone()[0] == 0
    con.close()


def test_rebuild_spec_meta_skips_unreadable_file(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """单个规则文件读不出 → 跳过该行继续建表, 不让一个坏文件毁掉整张 spec_meta。"""
    m = _spec(mem_ws, monkeypatch)
    good = _write_rule(mem_ws, "rules", "git", "good",
                       "title: good\ncategory: git\nkeywords: []\nstatus: active\ninclusion: auto\n",
                       "## 好规则\n\nok\n")
    bad = _write_rule(mem_ws, "rules", "git", "bad",
                      "title: bad\ncategory: git\nkeywords: []\nstatus: active\ninclusion: auto\n",
                      "## 坏规则\n\nx\n")
    _make_unreadable(bad)
    try:
        m._rebuild_spec_meta()
        con = sqlite3.connect(m.root / ".recall.db")
        paths = {r[0] for r in con.execute("SELECT path FROM spec_meta").fetchall()}
        con.close()
        assert str(good.relative_to(m.root)) in paths
        assert str(bad.relative_to(m.root)) not in paths
    finally:
        bad.chmod(0o644)


def _map_page(ws: Path, topic: str, fm: str, body: str) -> Path:
    return _write_rule(ws, "map", "code", topic, fm, body)


def test_recall_src_code_hits_and_summarizes_anchors(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """--src code 命中 map 语义页 → 输出命中行 + 按频次排序的 anchors 汇总。"""
    m = _spec(mem_ws, monkeypatch)
    _map_page(mem_ws, "svc",
              "title: svc\ncategory: code\nkeywords: [dispatcher]\nstatus: active\n"
              "inclusion: auto\nanchors: a/x.py,b/y.py\n",
              "## 调度层\n\ndispatcher 说明\n")
    _map_page(mem_ws, "svc2",
              "title: svc2\ncategory: code\nkeywords: [dispatcher]\nstatus: active\n"
              "inclusion: auto\nanchors: a/x.py\n",
              "## 调度层二\n\ndispatcher 补充\n")
    m._reindex_all()
    m.recall(argparse.Namespace(query="dispatcher", src="code"))
    out = capsys.readouterr().out
    assert "map namespace code 语义页" in out
    assert "- a/x.py (2次命中)" in out  # 两页共享 → 频次 2 排最前
    assert "- b/y.py (1次命中)" in out


def test_recall_map_code_degrades_to_grep_on_broken_table(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """map code 召回同样有 grep 降级路: rules 表缺失时不抛, 退回扫 map/index.md。"""
    m = _spec(mem_ws, monkeypatch)
    _map_page(mem_ws, "svc",
              "title: svc\ncategory: code\nkeywords: [dispatcher]\nstatus: active\ninclusion: auto\n",
              "## 调度层\n\ndispatcher 说明\n")
    m._reindex_all()
    con = sqlite3.connect(m.root / ".recall.db")
    con.execute("DROP TABLE rules")
    con.commit()
    con.close()
    assert any("dispatcher" in h for h in m._recall_map_code("dispatcher"))
    assert m._summarize_anchors("dispatcher") == ""  # 同一异常路: anchors 汇总返空串


def test_summarize_anchors_edge_cases(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """anchors 汇总的三条空返回路: 无 db / 查询含双引号 / 命中页都没写 anchors。"""
    m = _spec(mem_ws, monkeypatch)
    assert m._summarize_anchors("x") == ""  # .recall.db 尚未建
    _map_page(mem_ws, "svc",
              "title: svc\ncategory: code\nkeywords: [dispatcher]\nstatus: active\ninclusion: auto\n",
              "## 调度层\n\ndispatcher 说明\n")
    m._reindex_all()
    assert m._summarize_anchors('"dispatcher') == ""  # 双引号破坏 MATCH → 提前返空
    assert m._summarize_anchors("dispatcher") == ""   # 命中但页上无 anchors


# ══════════════════════ map.py ══════════════════════

def test_map_paths_injection_and_non_file_skipped(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """--paths 注入清单 (免依赖真 git 仓); 清单里不存在的条目跳过不算数。"""
    (mem_ws / "sample.py").write_text("def alpha():\n    pass\n\nclass Beta:\n    pass\n")
    _spec(mem_ws, monkeypatch).map(
        argparse.Namespace(skeleton=True, paths="sample.py,does/not/exist.py"))
    data = json.loads(capsys.readouterr().out)
    assert data["total_files"] == 1
    assert data["files"][0]["symbols"] == ["alpha", "Beta"]


def test_map_empty_paths_returns_zero(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """清单注入后一个有效路径都没有 → 零文件零行, 不去偷偷回落 git ls-files。"""
    _spec(mem_ws, monkeypatch).map(argparse.Namespace(skeleton=True, paths=",,"))
    assert json.loads(capsys.readouterr().out) == {"total_files": 0, "total_lines": 0, "files": []}


def test_map_skips_binary_file(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """二进制文件读不成文本 → 跳过而非炸掉整次 map。"""
    (mem_ws / "blob.bin").write_bytes(b"\xff\xfe\x00\x01")
    (mem_ws / "ok.py").write_text("def gamma():\n    pass\n")
    _spec(mem_ws, monkeypatch).map(argparse.Namespace(skeleton=True, paths="blob.bin,ok.py"))
    data = json.loads(capsys.readouterr().out)
    assert [f["path"] for f in data["files"]] == ["ok.py"]


def test_map_without_map_namespace_outputs_skeleton_only(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """map namespace 目录不存在 → 不带 --skeleton 也只出骨架 (无语义页时零回归)。"""
    import shutil as _shutil
    m = _spec(mem_ws, monkeypatch)
    _shutil.rmtree(m.root / "map")
    (mem_ws / "sample.py").write_text("def alpha():\n    pass\n")
    m.map(argparse.Namespace(skeleton=False, paths="sample.py"))
    data = json.loads(capsys.readouterr().out)
    assert "merged" not in data and data["total_files"] == 1


def test_map_merges_semantic_pages_and_skips_unreadable(
        mem_ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """有 map 语义页 → 骨架与语义合并输出; 读不出的语义页跳过不影响其余。"""
    m = _spec(mem_ws, monkeypatch)
    _map_page(mem_ws, "svc",
              "title: svc\ncategory: code\nkeywords: [a]\nstatus: active\ninclusion: auto\n",
              "## 调度层\n\n说明\n")
    bad = _map_page(mem_ws, "bad",
                    "title: bad\ncategory: code\nkeywords: []\nstatus: active\ninclusion: auto\n",
                    "## 坏页\n\nx\n")
    _make_unreadable(bad)
    try:
        (mem_ws / "sample.py").write_text("def alpha():\n    pass\n")
        m.map(argparse.Namespace(skeleton=False, paths="sample.py"))
        data = json.loads(capsys.readouterr().out)
        assert data["merged"] is True
        assert [p["path"] for p in data["semantic"]["code"]] == ["code/svc.md"]
    finally:
        bad.chmod(0o644)


def test_map_parse_frontmatter_array_forms(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """map 语义页 frontmatter 的两种数组写法都要解析: 行内 `[a,b]` 与流式 `- item`。"""
    meta = _spec(mem_ws, monkeypatch)._parse_frontmatter(
        "---\n"
        "title: svc\n"
        "category: code\n"
        "keywords:\n"
        "  - dispatcher\n"
        "  - router\n"
        "anchors: [a/x.py, b/y.py]\n"
        "inclusion: auto\n"
        "---\n\n正文\n")
    assert meta["keywords"] == ["dispatcher", "router"]
    assert meta["anchors"] == ["a/x.py", "b/y.py"]


def test_map_parse_frontmatter_flow_anchors(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """anchors 也支持流式数组 (与 keywords 对称), 否则 maintain 断链判据会全盲。"""
    meta = _spec(mem_ws, monkeypatch)._parse_frontmatter(
        "---\nanchors:\n  - a/x.py\n  - b/y.py\n---\n\n正文\n")
    assert meta["anchors"] == ["a/x.py", "b/y.py"]
