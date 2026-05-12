#!/usr/bin/env python3
"""save_session.py — cortex 会话落档核心。

由 stop.sh / post_compact.sh / cortex-save skill / /cortex:save 复用。

输入:
  --vault PATH        Obsidian vault 绝对路径 (必需)
  --transcript PATH   CC transcript jsonl 路径 (Stop / SubagentStop / PostCompact 提供)
  --reason REASON     stop | subagent-stop | compact | manual
  --tail N            读 transcript 末尾 N 条 (默认 30)
  --dry-run           不写文件, 只打印计划
  --title TITLE       手动指定标题 (manual reason 时常用)
  --body PATH         手动从文件读正文 (manual reason 时可选)

退出码:
  0  已写入 (stdout = 落档绝对路径)
  2  未触发 (不平凡度不够 / 已 stop_hook_active 等; stdout 空)
  1  失败 (stderr = 简短原因)

仅依赖 python stdlib。
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

# ---------- 启发式: 关键词 + 评分 ----------

KEYWORDS = (
    "debug",
    "fix",
    "decision",
    "architecture",
    "config",
    "tradeoff",
    "trade-off",
    "regression",
    "race",
    "deadlock",
    "leak",
    "架构",
    "决策",
    "配置",
    "修复",
    "取舍",
    "复盘",
    "排错",
    "踩坑",
)

# file:line 形式 (e.g. src/foo.py:123 / lib/bar.rs:42-50)
FILE_LINE_RE = re.compile(r"\b[\w./\-]+\.[A-Za-z]{1,5}:\d+(?:-\d+)?\b")
# git diff hunk header
DIFF_RE = re.compile(r"^(?:diff --git |@@ )", re.MULTILINE)
# inline code block / fenced block start
CODE_FENCE_RE = re.compile(r"^```[a-zA-Z]+", re.MULTILINE)


def heuristic_score(text: str) -> dict[str, int]:
    """返回评分细节 (调试用), 不直接判定。"""
    lower = text.lower()
    kw_hits = sum(lower.count(k) for k in KEYWORDS)
    file_line_hits = len(FILE_LINE_RE.findall(text))
    diff_hits = len(DIFF_RE.findall(text))
    fence_hits = len(CODE_FENCE_RE.findall(text))
    return {
        "kw": kw_hits,
        "file_line": file_line_hits,
        "diff": diff_hits,
        "code_fence": fence_hits,
    }


def is_nontrivial(score: dict[str, int]) -> bool:
    """判定阈值: ≥2 关键词 OR ≥3 file:line 引用 OR ≥1 diff 块。"""
    if score["kw"] >= 2:
        return True
    if score["file_line"] >= 3:
        return True
    if score["diff"] >= 1:
        return True
    return False


# ---------- transcript 解析 ----------


def read_transcript_tail(path: Path, n: int) -> list[dict[str, Any]]:
    """jsonl 行式; 返回末尾 n 条已解析 dict (跳过坏行)。"""
    if not path.is_file():
        return []
    try:
        # 简单读全文; CC transcript 通常 < 10MB, 不优化
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for ln in lines[-n * 3 :]:  # 多读一些, 防止包装行
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out[-n:]


def extract_text_from_entry(entry: dict[str, Any]) -> str:
    """从 transcript 一条记录抽取可见文本 (user prompt / assistant text)。"""
    # 兼容多种 schema: {role, content} / {type, message:{...}}
    msg = entry.get("message") or entry
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") in ("text", "tool_result"):
                t = c.get("text") or c.get("content") or ""
                if isinstance(t, list):
                    for inner in t:
                        if isinstance(inner, dict) and inner.get("type") == "text":
                            chunks.append(str(inner.get("text", "")))
                else:
                    chunks.append(str(t))
            elif c.get("type") == "tool_use":
                # 不要泄漏完整 tool_input, 仅记录工具名
                chunks.append(f"[tool_use:{c.get('name', '?')}]")
        return "\n".join(chunks)
    return ""


def collect_transcript_text(entries: Iterable[dict[str, Any]]) -> str:
    parts = []
    for e in entries:
        t = extract_text_from_entry(e)
        if t:
            parts.append(t)
    return "\n\n".join(parts)


# ---------- 摘要抽取 ----------


def last_user_prompt(entries: list[dict[str, Any]]) -> str:
    for e in reversed(entries):
        msg = e.get("message") or e
        if msg.get("role") == "user" or e.get("type") == "user":
            txt = extract_text_from_entry(e).strip()
            # 跳过纯 tool_result
            if txt and not txt.startswith("[tool_use:"):
                return txt[:500]
    return ""


def last_assistant_text(entries: list[dict[str, Any]]) -> str:
    for e in reversed(entries):
        msg = e.get("message") or e
        if msg.get("role") == "assistant" or e.get("type") == "assistant":
            txt = extract_text_from_entry(e).strip()
            if txt:
                return txt[:1500]
    return ""


def collect_modified_files(text: str) -> list[str]:
    """从 transcript 文本启发式抽 file:line 引用。"""
    seen: list[str] = []
    for m in FILE_LINE_RE.findall(text):
        path_only = m.split(":")[0]
        if path_only not in seen:
            seen.append(path_only)
        if len(seen) >= 12:
            break
    return seen


# ---------- 路径 / 文件名 ----------


SLUG_BAD = re.compile(r"[^\w\s-]+", re.UNICODE)
SLUG_WS = re.compile(r"[\s_]+")


def slugify(text: str, max_len: int = 40) -> str:
    if not text:
        return "session"
    # 保留中英文; 去禁用字符 (prd §3.2.7: : \ / | ? * < > " 等)
    text = unicodedata.normalize("NFKC", text)
    # 取首行 / 首句
    text = text.strip().splitlines()[0]
    text = re.sub(r'[\:\\/|?*<>"]+', " ", text)
    text = SLUG_BAD.sub("", text)
    text = SLUG_WS.sub("-", text).strip("-").lower()
    if not text:
        text = "session"
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "session"


def sha8(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8", errors="replace")).hexdigest()[:8]


def read_preset(vault: Path) -> str:
    vfile = vault / "_meta" / "version.json"
    if vfile.is_file():
        try:
            return str(json.loads(vfile.read_text(encoding="utf-8")).get("preset") or "blank")
        except Exception:
            return "blank"
    return "blank"


def read_vault_meta(vault: Path) -> dict[str, Any]:
    """Read full _meta/version.json. Returns {} on failure."""
    vfile = vault / "_meta" / "version.json"
    if vfile.is_file():
        try:
            data = json.loads(vfile.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def read_vault_lang(vault: Path) -> str:
    """Resolve lang: vault _meta/version.json > config.lang > zh-CN.

    Env var lookup removed per PRD (config-only).
    """
    meta_lang = read_vault_meta(vault).get("lang")
    if isinstance(meta_lang, str) and meta_lang:
        return meta_lang
    try:
        from cortex_config import load_config
        cfg_lang = load_config().get("lang")
        if isinstance(cfg_lang, str) and cfg_lang:
            return cfg_lang
    except ImportError:
        pass
    return "zh-CN"


def backup_transcript(vault: Path, transcript: Path, when: dt.datetime, slug: str, cli: str) -> Path | None:
    """Copy raw transcript to <vault>/sessions/<cli>/<YYYY-MM>/<DD-HHMM>-<slug>.jsonl.

    Only when _meta/version.json:.preserve_transcript == true. Returns dest path or None.
    """
    meta = read_vault_meta(vault)
    if not bool(meta.get("preserve_transcript")):
        return None
    if not transcript.is_file():
        return None
    folder = vault / "sessions" / cli / when.strftime("%Y-%m")
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{when.strftime('%d-%H%M')}-{slug}.jsonl"
    dest = folder / name
    counter = 2
    while dest.exists():
        dest = folder / f"{when.strftime('%d-%H%M')}-{slug}-{counter}.jsonl"
        counter += 1
        if counter > 50:
            break
    try:
        raw = transcript.read_text(encoding="utf-8", errors="replace")
        try:
            from masking import mask as _mask

            masked, _ = _mask(raw)
        except Exception:
            # 脱敏失败 -> 拒绝备份 (fail-closed), 避免明文 secret 落档
            return None
        dest.write_text(masked, encoding="utf-8")
        return dest
    except Exception:
        return None


# ---------- block-id 注入 ----------

H2_H3_RE = re.compile(r"^(#{2,3} .+?)$", re.MULTILINE)
EXISTING_BLOCK_RE = re.compile(r"\^cortex-([0-9a-f]{8})", re.IGNORECASE)


def inject_block_ids(body: str, seed_prefix: str, used: set[str]) -> str:
    """每个 H2/H3 段落末尾 (下个 heading 或 EOF 前) 加 ^cortex-<sha8>。"""
    # 切分为 (heading, body) 对
    parts = re.split(r"(^#{2,3} .+$)", body, flags=re.MULTILINE)
    if len(parts) <= 1:
        return body
    out: list[str] = [parts[0]]
    section_idx = 0
    i = 1
    while i < len(parts):
        heading = parts[i]
        section = parts[i + 1] if i + 1 < len(parts) else ""
        section_idx += 1
        seed = f"{seed_prefix}::{section_idx}::{heading}"
        bid = sha8(seed)
        # 冲突则递增
        attempts = 0
        while bid in used and attempts < 16:
            attempts += 1
            bid = sha8(f"{seed}::{attempts}")
        used.add(bid)
        # 在 section 末尾 (trailing 空行前) 插入 ^id
        section_stripped = section.rstrip()
        suffix = section[len(section_stripped) :]
        if section_stripped:
            section_new = f"{section_stripped} ^cortex-{bid}{suffix or chr(10)}"
        else:
            section_new = f"\n^cortex-{bid}\n"
        out.append(heading)
        out.append(section_new)
        i += 2
    return "".join(out)


# ---------- 摘要 → markdown body ----------

REASON_LABEL = {
    "stop": "Stop hook 自动落档",
    "subagent-stop": "SubagentStop 自动落档",
    "compact": "PostCompact 摘要落档",
    "manual": "手动落档",
}


def build_body(
    *,
    reason: str,
    title: str,
    user_prompt: str,
    assistant_text: str,
    files: list[str],
    score: dict[str, int],
    lang: str = "zh-CN",
    cli: str = "claude-code",
    cli_session: str = "",
) -> str:
    label = REASON_LABEL.get(reason, reason)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        "type: log",
        f"title: {title}",
        "aliases: []",
        "tags: [log, cortex-auto]",
        f"created: {today}",
        f"updated: {today}",
        "preset: {{PRESET}}",
        f"lang: {lang}",
        f"cli: {cli}",
        f"cli_session: {cli_session}",
        f"reason: {reason}",
        "---",
        "",
        f"# {title}",
        "",
        "> [!info]+ 来源",
        f"> {label} · UTC {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}",
        "",
    ]

    if user_prompt:
        lines.extend(
            [
                "## 提问 / 触发",
                "",
                "> [!quote]",
                *[f"> {ln}" for ln in user_prompt.splitlines() if ln.strip()],
                "",
            ]
        )

    if assistant_text:
        lines.extend(
            [
                "## 结论 / 关键回复",
                "",
                assistant_text.strip(),
                "",
            ]
        )

    if files:
        lines.append("## 涉及文件")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")

    lines.extend(
        [
            "## 启发式评分",
            "",
            f"- 关键词命中: {score['kw']}",
            f"- file:line 引用: {score['file_line']}",
            f"- diff 块: {score['diff']}",
            f"- 代码块: {score['code_fence']}",
            "",
        ]
    )

    return "\n".join(lines)


# ---------- index / hot 同步 ----------


def update_log_index(vault: Path, rel_path: str, title: str) -> None:
    idx = vault / "log" / "_index.md"
    line = f"- [[{rel_path}|{title}]]"
    try:
        if idx.is_file():
            existing = idx.read_text(encoding="utf-8", errors="replace")
            if line in existing:
                return
            new = existing.rstrip() + "\n" + line + "\n"
        else:
            idx.parent.mkdir(parents=True, exist_ok=True)
            new = f"# 会话日志索引\n\n{line}\n"
        idx.write_text(new, encoding="utf-8")
    except Exception:
        pass


HOT_RECENT_HEADER = "## 最近落档"
HOT_MAX_RECENT = 5


def update_hot(vault: Path, rel_path: str, title: str) -> None:
    hot = vault / "hot.md"
    bullet = f"- [[{rel_path}|{title}]]"
    try:
        if hot.is_file():
            text = hot.read_text(encoding="utf-8", errors="replace")
        else:
            text = (
                "---\ntype: meta\ntitle: hot\ntags: [meta]\n---\n\n# hot\n\n"
                + HOT_RECENT_HEADER
                + "\n\n"
            )
        if HOT_RECENT_HEADER not in text:
            text = text.rstrip() + f"\n\n{HOT_RECENT_HEADER}\n\n"

        head, _, tail = text.partition(HOT_RECENT_HEADER)
        # tail 形如 "\n\n- ...\n- ...\n\n## 其他 ..."
        # 取紧随其后的 bullet 段
        tail_lines = tail.splitlines()
        # 跳过 header 行后的空行
        bullets: list[str] = []
        rest_start = 0
        for i, ln in enumerate(tail_lines):
            if ln.startswith("- "):
                bullets.append(ln)
            elif ln.strip() == "" and not bullets:
                continue
            else:
                rest_start = i
                break
        else:
            rest_start = len(tail_lines)
        # 去重 + 置顶
        bullets = [b for b in bullets if b != bullet]
        bullets.insert(0, bullet)
        bullets = bullets[:HOT_MAX_RECENT]
        rest = "\n".join(tail_lines[rest_start:]) if rest_start < len(tail_lines) else ""
        new_tail = "\n" + "\n".join(bullets) + "\n"
        if rest.strip():
            new_tail += "\n" + rest.lstrip("\n")
        hot.write_text(head + HOT_RECENT_HEADER + new_tail, encoding="utf-8")
    except Exception:
        pass


# ---------- obsidian-git 协调 ----------


def has_obsidian_git(vault: Path) -> bool:
    return (vault / ".obsidian" / "plugins" / "obsidian-git" / "data.json").is_file()


# ---------- 主流程 ----------


def determine_target(
    vault: Path, *, when: dt.datetime, slug: str, reason: str
) -> tuple[Path, str]:
    """返回 (绝对路径, 相对 vault 的路径字符串)。"""
    suffix = "compact" if reason == "compact" else slug
    # path: log/YYYY-MM/DD-HHMM-<slug>.md
    folder = vault / "log" / when.strftime("%Y-%m")
    name = f"{when.strftime('%d-%H%M')}-{suffix}.md"
    abs_path = folder / name
    rel = f"log/{when.strftime('%Y-%m')}/{name[:-3]}"  # wikilink 不带 .md
    # 冲突: 加序号
    counter = 2
    while abs_path.exists():
        name = f"{when.strftime('%d-%H%M')}-{suffix}-{counter}.md"
        abs_path = folder / name
        rel = f"log/{when.strftime('%Y-%m')}/{name[:-3]}"
        counter += 1
        if counter > 50:
            break
    return abs_path, rel


def collect_existing_block_ids(vault: Path) -> set[str]:
    """扫 log/ 与 folds/ 已有 ^cortex-<sha8>, 防冲突。"""
    seen: set[str] = set()
    for sub in ("log", "folds"):
        d = vault / sub
        if not d.is_dir():
            continue
        for p in d.rglob("*.md"):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for m in EXISTING_BLOCK_RE.findall(txt):
                seen.add(m.lower())
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--transcript", default="")
    ap.add_argument("--reason", default="manual",
                    choices=["stop", "subagent-stop", "compact", "manual"])
    ap.add_argument("--tail", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--title", default="")
    ap.add_argument("--body", default="")
    ap.add_argument("--force", action="store_true",
                    help="跳过启发式判定 (manual 模式默认 force)")
    ap.add_argument("--cli", default="claude-code",
                    choices=["claude-code", "codex", "copilot", "gemini",
                             "qoder", "kiro", "manual"],
                    help="来源 CLI (写入 frontmatter cli 字段)")
    ap.add_argument("--cli-session", default="",
                    help="来源会话 id (写入 frontmatter cli_session 字段)")
    args = ap.parse_args()

    vault = Path(os.path.expanduser(args.vault)).resolve()
    if not vault.is_dir():
        print(f"vault not found: {vault}", file=sys.stderr)
        return 1

    # ----- transcript 读取 + 评分 -----
    entries: list[dict[str, Any]] = []
    text = ""
    if args.transcript:
        tp = Path(os.path.expanduser(args.transcript))
        entries = read_transcript_tail(tp, args.tail)
        text = collect_transcript_text(entries)

    # body 文件覆盖
    body_override = ""
    if args.body:
        bp = Path(os.path.expanduser(args.body))
        if bp.is_file():
            body_override = bp.read_text(encoding="utf-8", errors="replace")

    score = heuristic_score(text + "\n" + body_override)

    # 触发判定
    if args.reason in ("stop", "subagent-stop") and not args.force:
        if not is_nontrivial(score):
            return 2
    # compact / manual 总是落档

    # ----- 摘要 -----
    user_p = last_user_prompt(entries) if entries else ""
    asst_t = last_assistant_text(entries) if entries else ""
    files = collect_modified_files(text)

    # ----- 标题 + 路径 -----
    when = dt.datetime.now(dt.timezone.utc)
    title_seed = args.title or user_p or asst_t.split("\n", 1)[0] or args.reason
    title_seed = title_seed.strip().splitlines()[0] if title_seed else args.reason
    if len(title_seed) > 60:
        title_seed = title_seed[:60].rstrip()
    if not title_seed:
        title_seed = REASON_LABEL.get(args.reason, args.reason)

    slug = slugify(args.title or user_p or asst_t.split("\n", 1)[0] or args.reason)
    abs_path, rel_path = determine_target(vault, when=when, slug=slug, reason=args.reason)

    # ----- locale + cli metadata -----
    lang = read_vault_lang(vault)

    # ----- body -----
    if body_override:
        body = body_override
    else:
        body = build_body(
            reason=args.reason,
            title=title_seed,
            user_prompt=user_p,
            assistant_text=asst_t,
            files=files,
            score=score,
            lang=lang,
            cli=args.cli,
            cli_session=args.cli_session,
        )

    preset = read_preset(vault)
    body = body.replace("{{PRESET}}", preset)

    # ----- P0 secret 脱敏 (落档前) -----
    try:
        from masking import mask as _mask  # 同目录模块, 纯 stdlib

        body, _mask_hits = _mask(body)
        if _mask_hits:
            # 仅记规则名计数, 严禁原值入日志
            from collections import Counter as _Counter

            _counts = _Counter(_mask_hits)
            _summary = ",".join(f"{n}x{c}" for n, c in sorted(_counts.items()))
            print(f"masking: redacted {_summary}", file=sys.stderr)
    except Exception:
        # fail-open 不能, transcript 必须脱敏 -> 异常时改 fail-closed 拒绝写入
        print("masking: module load failed, aborting save", file=sys.stderr)
        return 1

    # ----- block-id 注入 -----
    used = collect_existing_block_ids(vault)
    seed_prefix = f"{rel_path}::{when.isoformat()}"
    body = inject_block_ids(body, seed_prefix, used)

    # ----- obsidian-git 协调 (prd §10.8) -----
    if has_obsidian_git(vault):
        body = body.rstrip() + "\n\n<!-- cortex-pending-commit -->\n"

    if args.dry_run:
        print(str(abs_path))
        return 0

    # ----- 写文件 -----
    try:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(body, encoding="utf-8")
    except Exception as e:
        print(f"write failed: {e}", file=sys.stderr)
        return 1

    # ----- 同步 index / hot -----
    update_log_index(vault, rel_path, title_seed)
    update_hot(vault, rel_path, title_seed)

    # ----- 原始 transcript 备份 (仅 _meta.preserve_transcript=true 时) -----
    if args.transcript:
        try:
            tp = Path(os.path.expanduser(args.transcript))
            if tp.is_file():
                backup_transcript(vault, tp, when, slug, args.cli)
        except Exception:
            pass

    # ----- 反向 wikilink 回填 (失败仅日志, 不阻断) -----
    try:
        import subprocess

        backlink_script = Path(__file__).parent / "backlink_sync.py"
        if backlink_script.is_file():
            subprocess.run(
                [
                    sys.executable,
                    str(backlink_script),
                    "--vault",
                    str(vault),
                    "--source",
                    rel_path,
                    "--quiet",
                ],
                timeout=10,
                check=False,
                capture_output=True,
            )
    except Exception:
        pass

    print(str(abs_path))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:  # 顶层兜底, 避免阻断 hook
        print(f"unexpected: {e}", file=sys.stderr)
        sys.exit(1)
