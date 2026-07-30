"""体检 / 降级 / 归档 / 恢复 / 重构 + `.audit-log`。

判据按 namespace 分表 (`MAINTAIN_POLICY`), 见 model.py。`--apply` 才动盘, 缺省只报告。

**一切动作可逆**: 归档是 move 到 `.archive/<ts>/` 而非删除, `restore <ts>` 可回滚 (撞名不覆盖
新规则, 加 `restored-` 前缀并存)。`degrade` 只改 frontmatter 的 `inclusion` 一行, **不搬文件**
—— inclusion 已脱离目录, 跨 namespace 搬文件既无意义又会让同时命中 stale 的文件在归档阶段
拿到失效路径 (历史上真炸过 FileNotFoundError)。
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Any, Optional, cast

from skeinlib.errors import SkeinError
from skeinlib.spec.model import (AUDIT_RETENTION_DAYS, DEFAULT_MAINTAIN_POLICY,
                                 KEYWORDS_DUP_THRESHOLD, MAINTAIN_POLICY, STALE_DAYS,
                                 always_budget, now)
from skeinlib.spec.text import (_clean_body, _frontmatter, _link_target, _months, _sections,
                                _strip_frontmatter)


class MaintainMixin:
    # ---- archive (完全重构前可逆清库: 移旧规则到 .archive/<ts>/, reindex 空) ----
    def archive(self, a: argparse.Namespace) -> None:
        namespace_opt = cast(Optional[str], getattr(a, "namespace", None))
        namespaces = [namespace_opt] if namespace_opt else self._scan_namespaces()
        ts = str(now())
        dest = self.root / ".archive" / ts
        moved = 0
        for ns in namespaces:
            for f in self._rule_files(ns):  # rglob 不含 .archive (在 root 下非 namespace 下)
                tgt = dest / f.relative_to(self.root)  # 保 <namespace>/<category>/ 结构
                tgt.parent.mkdir(parents=True, exist_ok=True)
                f.rename(tgt)  # 同 fs move, 不复制
                moved += 1
        self._reindex_all()
        if moved:
            print(f"已归档 {moved} 条规则 → {dest}\n回滚: python3 spec.py restore {ts}")
        else:
            print("无规则可归档 (库已空)")
    # ---- restore (从归档恢复; 撞名的旧规则加 restored- 前缀不覆盖重构后新规则) ----
    def restore(self, a: argparse.Namespace) -> None:
        ts = cast(str, a.ts)
        src = self.root / ".archive" / ts
        if not src.exists():
            raise SkeinError(f"归档不存在: {src} (查可用: ls {self.root / '.archive'})")
        moved = 0
        for f in sorted(src.rglob("*.md")):
            if f.name == "index.md":
                continue
            tgt = self.root / f.relative_to(src)
            tgt.parent.mkdir(parents=True, exist_ok=True)
            if tgt.exists():  # 重构后同路径已有新规则 → 不覆盖, 换名并存
                tgt = tgt.with_name(f"restored-{f.name}")
            f.rename(tgt)
            moved += 1
        self._reindex_all()
        print(f"已恢复 {moved} 条 ← {src}")
    # ---- maintain (全量体检, 判据按 namespace 分表 — design.md §4, MAINTAIN_POLICY 单一实现) ----
    def _scan_findings(self, namespaces: list[str]) -> list[dict[str, Any]]:
        """全量扫描 → 结构化 findings (kind/text + 修复所需上下文); maintain 报告 & --apply 共用。

        每 namespace 按 MAINTAIN_POLICY.get(ns, DEFAULT_MAINTAIN_POLICY) 决定哪些判据生效
        (rules/未列名 namespace 走全量默认判据; product/map/external 见分表)。
        超预算/断链(含 anchors)/fileMatch 缺 globs 三项与 namespace 无关, 全 namespace 统一跑。"""
        # 合法 wikilink 目标 = 主题 stem (整篇) ∪ stem#规则标题 (单条); 用全库扫描, 不受 --namespace 过滤影响
        all_ns = self._scan_namespaces()
        all_slugs = {f.stem for ns in all_ns for f in self._rule_files(ns)} | \
                    {f"{f.stem}#{t}" for ns in all_ns for f, t, _ in self._rules(ns)}
        backlinks = self._rebuild_backlinks()  # 一次扫, 孤立判据复用
        now_ts = now()
        mtimes = self._mtimes()
        repo_root = self.root.parent.parent  # .skein/spec → 仓库根 (anchors 是仓库相对路径)
        findings: list[dict[str, Any]] = []

        # 判据 (全部): 超预算 — always 页总字符, 与 --namespace 过滤无关 (跨 namespace 全局关切), 恒跑
        core_text = self._core_text_raw()
        budget = always_budget()
        if len(core_text) > budget:
            sized = sorted(
                ((len(_strip_frontmatter(f.read_text()).strip()), f.parent.name, f.stem)
                 for f in self._always_files()), reverse=True)
            cands = ", ".join(f"{cat}/{stem}({sz})" for sz, cat, stem in sized[:3])
            findings.append({"kind": "overbudget", "size": len(core_text),
                             "text": f"[超预算] always {len(core_text)} > {budget} 字符 — 考虑降级: {cands}"})

        for ns in namespaces:
            policy = MAINTAIN_POLICY.get(ns, DEFAULT_MAINTAIN_POLICY)
            for f in self._rule_files(ns):
                txt = f.read_text()
                meta = _frontmatter(txt)
                rel = f"{ns}/{f.parent.name}/{f.stem}"
                status = meta.get("status", "active")
                age = self._age_days(f, mtimes, now_ts)

                # 判据 rules: stale — 最近修改 (git 提交时间, 无则 fs mtime) 超 STALE_DAYS 且无引用
                if policy.get("stale") and age > STALE_DAYS:
                    findings.append({"kind": "stale", "file": f, "rel": rel, "status": status,
                                     "text": f"[stale] {rel} (最近改动 {_months(age)},{age}天前, status {status})"})

                # 判据 (全部): broken wikilink — body 的 [[slug]] 目标不在库内 (只报告, 需人判断修哪头)
                body = _strip_frontmatter(txt)
                for m in re.finditer(r"\[\[([^\]]+)\]\]", body):
                    slug = m.group(1).strip()
                    tgt = _link_target(slug)
                    if tgt and tgt not in all_slugs:
                        findings.append({"kind": "broken_link", "rel": rel, "slug": slug,
                                         "text": f"[断链] {rel}: [[{slug}]] ✗ 目标缺失"})

                # 判据 (全部, 断链判据扩到 anchors): anchors 声明路径不存在 → 统一只报告;
                # namespace 判据表另标 "archive" 时 (如 map) 追加一条可自动归档的 finding。
                anchors_raw = str(meta.get("anchors", "")).strip()
                if anchors_raw:
                    missing = [a.strip() for a in anchors_raw.split(",")
                              if a.strip() and not (repo_root / a.strip()).exists()]
                    if missing:
                        findings.append({"kind": "broken_link", "rel": rel,
                                         "text": f"[断链] {rel}: anchors {','.join(missing)} 路径不存在"})
                        if policy.get("anchors") == "archive":
                            findings.append({"kind": "anchors_broken", "file": f, "rel": rel,
                                             "text": f"[anchors失效] {rel} (namespace={ns}) — 判据: 自动归档"})

                # 判据 rules/external: 废弃/superseded → archive
                if policy.get("deprecated") and status in ("deprecated", "superseded"):
                    findings.append({"kind": "deprecated", "file": f, "rel": rel, "status": status,
                                     "text": f"[废弃] {rel} (status {status}) — 建议 archive"})

                # 判据 (全部): inclusion=fileMatch 缺 globs → 只报告为配置问题
                if self._inclusion(f) == "fileMatch" and not str(meta.get("globs", "")).strip():
                    findings.append({"kind": "config_issue", "rel": rel,
                                     "text": f"[配置问题] {rel}: inclusion=fileMatch 缺 globs"})

                # 判据 rules: 孤立 — 整篇无入度 (stem 及其任一章节都不在 backlinks) + active + 超 STALE_DAYS
                if policy.get("orphan") and status == "active":
                    linked = f.stem in backlinks or any(f"{f.stem}#{t}" in backlinks
                                                        for t, _ in _sections(txt))
                    if not linked and age > STALE_DAYS:
                        findings.append({"kind": "orphan", "file": f, "rel": rel,
                                         "text": f"[孤立] {rel} 无入度+active+超{STALE_DAYS}天 — 候选归档/降级"})

            # 判据 rules: keywords 高重复 — 同 keywords 组 ≥3 条 → 保留最新, 余 archive
            if policy.get("keywords_dup"):
                groups: dict[str, list[Path]] = {}
                for f in self._rule_files(ns):
                    kw = _frontmatter(f.read_text()).get("keywords", "").strip()
                    if not kw:
                        continue
                    key = ",".join(sorted(k for k in kw.split(",") if k.strip()))
                    groups.setdefault(key, []).append(f)
                for kw_key, hits in sorted(groups.items()):
                    if len(hits) >= KEYWORDS_DUP_THRESHOLD:
                        rels = [f"{ns}/{f.parent.name}/{f.stem}" for f in hits]
                        findings.append({"kind": "keywords_dup", "kw": kw_key, "files": hits,
                                         "text": f'[重复 keywords] "{kw_key}" ×{len(hits)}: {", ".join(rels)}'})
        return findings
    def maintain(self, a: argparse.Namespace) -> None:
        namespace_opt = cast(Optional[str], getattr(a, "namespace", None))
        namespaces = [namespace_opt] if namespace_opt else self._scan_namespaces()
        apply = bool(getattr(a, "apply", False))
        findings = self._scan_findings(namespaces)

        if not apply:
            print("maintain 体检 (.skein/spec):")
            if findings:
                print("\n".join(fd["text"] for fd in findings))
            else:
                print("全清 (无超预算/stale/断链/重复/废弃/孤立)")
            return

        # --apply: 自动修复可修项 (断链/配置问题/report类判据只报告, 需人判断)
        broken = [fd for fd in findings if fd["kind"] == "broken_link"]
        report_only = [fd for fd in findings if fd["kind"] == "config_issue"]
        actions: list[str] = []

        # 超预算 → 循环降级 always→auto (仅改 frontmatter, 不移文件)
        if any(fd["kind"] == "overbudget" for fd in findings):
            before = len(self._core_text_raw())
            degraded = self._degrade_core_to_budget()
            after = len(self._core_text_raw())
            for rel in degraded:
                actions.append(f"降级 always→auto: {rel}")
            actions.append(f"always 超预算修复: {before}→{after} 字符 (降 {len(degraded)} 条)")

        # 归档批: stale + 废弃 + keywords 重复(保留最新) + anchors失效(仅 policy=archive 如 map) 合并一次 .archive/<ts>/
        archive_reasons: dict[Path, tuple[str, str]] = {}
        for fd in findings:
            if fd["kind"] == "stale":
                f = cast(Path, fd["file"])
                archive_reasons[f] = ("prune-stale", f"stale({fd['rel']},超{STALE_DAYS}天)")
            elif fd["kind"] == "deprecated":
                f = cast(Path, fd["file"])
                archive_reasons[f] = ("prune-deprecated", f"废弃(status={fd['status']})")
            elif fd["kind"] == "orphan":
                f = cast(Path, fd["file"])
                # ponytail: stale 必然 orphan, 但 stale 判据更强更具体 → stale 优先, orphan 不覆盖已占 key
                if f not in archive_reasons:
                    archive_reasons[f] = ("prune-orphan", "孤立(无入度+active+stale)")
            elif fd["kind"] == "anchors_broken":
                f = cast(Path, fd["file"])
                if f not in archive_reasons:
                    archive_reasons[f] = ("prune-anchors", f"anchors失效({fd['rel']})")
        for fd in findings:
            if fd["kind"] == "keywords_dup":
                files = cast(list[Path], fd["files"])
                # 保留最新 (最近改动者, git 提交时间优先), 其余归档
                mt = self._mtimes()
                newest = max(files, key=lambda f: mt.get(f, 0))
                for f in files:
                    if f != newest and f not in archive_reasons:
                        archive_reasons[f] = (
                            "prune-dup", f'keywords重复(组"{fd["kw"]}":{len(files)}条,保留最新)')
        # ponytail: 跳过被上文 degrade 处理的 (overbudget+stale 同一最大文件场景);
        # degrade 只改 inclusion 不移文件, 理论上不会消失, 此过滤仅兜底防御性检查。
        archive_reasons = {f: r for f, r in archive_reasons.items() if f.exists()}
        if archive_reasons:
            self._archive_batch(list(archive_reasons.keys()), archive_reasons)
            for f, (act, _reason) in archive_reasons.items():
                actions.append(f"归档 ({act}): {f.relative_to(self.root).as_posix()}")

        print("maintain --apply 已执行:")
        if actions:
            print("\n".join(actions))
        else:
            print("无自动可修项")
        need_human = broken + report_only
        if need_human:
            print("\n仍需人工 (断链/配置问题 — 需判断修哪头/补目标/补 globs):")
            print("\n".join(fd["text"] for fd in need_human))
    # ---- 审计日志 (.audit-log 追加写 + 7天轮转) ----
    def _write_audit(self, action: str, file: str, before: str, after: str, reason: str) -> None:
        """追加审计行 + 写前清 7 天前旧行 (按行首 iso ts 判)。格式: iso_ts|action|file|before->(after)|reason"""
        log = self.root / ".audit-log"
        cutoff = now() - AUDIT_RETENTION_DAYS * 86400
        kept: list[str] = []
        if log.exists():
            for ln in log.read_text().splitlines():
                head = ln.split("|", 1)[0]
                try:
                    if datetime.fromisoformat(head).timestamp() < cutoff:
                        continue  # 超 7 天 → 丢
                except ValueError:
                    pass  # 非 iso 头 (旧格式/手写) → 保留不误删
                kept.append(ln)
        iso_ts = datetime.fromtimestamp(now()).isoformat(timespec="seconds")
        kept.append(f"{iso_ts}|{action}|{file}|{before}->({after})|{reason}")
        log.write_text("\n".join(kept) + "\n")
    # ---- 单文件降级核心 (degrade 子命令 + maintain --apply 复用) ----
    def _degrade_one(self, f: Path, reason: str) -> str:
        """always→auto 单文件: 仅改 frontmatter inclusion 一行 + reindex + 审计, 不移动文件
        (inclusion 已脱离目录, 跨 namespace git mv 已无意义 — design.md §2)。返回文件相对路径 (不变)。"""
        if not f.exists():
            raise SkeinError(f"降级失败: 文件不存在 {f}")
        rel = f.relative_to(self.root).as_posix()
        self._rewrite_inclusion(f, "auto")
        self._write_audit("degrade", rel, "always", "auto", reason)
        self._reindex_all()
        return rel
    def _degrade_core_to_budget(self) -> list[str]:
        """循环降 top-1 最大 always 页 → auto, 直到 always 总字符 < always_budget() 或无 always 页。返回降级路径列表。"""
        degraded: list[str] = []
        while True:
            core_text = self._core_text_raw()
            budget = always_budget()
            if len(core_text) <= budget:
                break
            files = self._always_files()
            if not files:
                break
            top = max(files, key=lambda f: len(_strip_frontmatter(f.read_text()).strip()))
            reason = f"always超预算({len(core_text)}>{budget})"
            degraded.append(self._degrade_one(top, reason))
        return degraded
    def _rewrite_inclusion(self, f: Path, new_inclusion: str) -> None:
        """改 frontmatter 的 inclusion 字段为新值 (原地正则替换首处); 旧文件缺该字段
        (走 layer fallback, 见 _inclusion()) 则在 frontmatter 开头插入一行, 就地"毕业"为显式字段。"""
        txt = f.read_text()
        new = re.sub(r"^inclusion:\s*\S+", f"inclusion: {new_inclusion}", txt, count=1, flags=re.MULTILINE)
        if new == txt:
            new = re.sub(r"^(---\n)", rf"\1inclusion: {new_inclusion}\n", txt, count=1)
        f.write_text(new)
    def _archive_batch(self, files: list[Path], reasons: dict[Path, tuple[str, str]]) -> int:
        """批量归档多文件到同一 .archive/<ts>/ (保 <layer>/<cat>/ 结构) + reindex + 审计。"""
        ts = str(now())
        dest_base = self.root / ".archive" / ts
        moved = 0
        for f in files:
            rel_before = f.relative_to(self.root).as_posix()
            dest = dest_base / f.relative_to(self.root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            f.rename(dest)
            act, reason = reasons.get(f, ("archive", ""))
            self._write_audit(act, rel_before, rel_before, f".archive/{ts}/{rel_before}", reason)
            moved += 1
        if moved:
            self._reindex_all()
        return moved
    # ---- degrade 子命令 ----
    def degrade(self, a: argparse.Namespace) -> None:
        if getattr(a, "auto", False):
            before = len(self._core_text_raw())
            degraded = self._degrade_core_to_budget()
            after = len(self._core_text_raw())
            if degraded:
                print(f"自动降级 {len(degraded)} 条 always→auto (总字符 {before}→{after}):")
                for rel in degraded:
                    print(f"  - {rel}")
            else:
                print(f"无需降级 (always 页总字符 {after} ≤ {always_budget()})")
            return
        target = cast(str, a.file)
        # external 是终点层 (纯手动检索), degrade 仅 always→auto 单向 → 显式拒, 免用户误以为可降级
        if target.replace("\\", "/").lstrip().startswith("external/"):
            raise SkeinError("external namespace 是终点, degrade 仅 always→auto 单向 (external 不参与降级)")
        f = self._resolve_spec_file(target)
        inc = self._inclusion(f)
        if inc != "always":
            raise SkeinError(f"非 always 页 (inclusion={inc}), 仅 always 可降级: {target}")
        rel = self._degrade_one(f, "手动降级")
        print(f"已降级 always→auto → {rel}")
    def _resolve_spec_file(self, target: str) -> Path:
        """归一化降级目标路径: 补 `.md`; 接受 `<namespace>/<category>/<name>` 完整路径,
        或裸 `<category>/<name>` —— 后者**扫全部 namespace 找**, 不默认某一个。

        这里曾硬默认 `core/` (layer 时代 always 页惯居该目录的残留), 于是 `sediment` 明明写进
        `rules/`, `degrade rules 里的那条` 却报「文件不存在 → core/...」。namespace 是目录扫描
        得的自由值, 任何硬编码默认都会跟实际库漂移。命中多个 namespace 时报错并列出候选, 不猜。
        """
        t = target.replace("\\", "/").strip("/")
        if not t.endswith(".md"):
            t += ".md"
        if t.count("/") >= 2:  # 已给完整 <namespace>/<category>/<name>
            f = self.root / t
            if not f.exists():
                raise SkeinError(f"文件不存在: {target} → {t}")
            return f
        hits = [self.root / ns / t for ns in self._scan_namespaces() if (self.root / ns / t).exists()]
        if not hits:
            raise SkeinError(
                f"文件不存在: {target} (已扫全部 namespace: {', '.join(self._scan_namespaces())}) — "
                f"需 <category>/<name> 或 <namespace>/<category>/<name> 形式")
        if len(hits) > 1:
            rels = ", ".join(h.relative_to(self.root).as_posix() for h in hits)
            raise SkeinError(f"{target} 在多个 namespace 下都存在: {rels} — 请给完整路径")
        return hits[0]
    # ---- restructure (碎片文件 → 主题文件合并; 源文件进 .archive/<ts>/ 可回滚) ----
    def restructure(self, a: argparse.Namespace) -> None:
        """--map 是 {目标主题文件相对路径: [源文件相对路径,...]} 的 JSON (主题归类由调用方语义判定)。

        每个源文件的每条规则 (章节, 旧库为整篇) 按序追加进目标主题文件, 标题保留原 title。
        """
        plan = json.loads(Path(cast(str, a.map)).read_text())
        dry = bool(getattr(a, "dry_run", False))
        srcs_all: list[Path] = []
        for target, srcs in plan.items():
            t = self.root / target
            layer, cat = t.relative_to(self.root).parts[0], t.parent.name
            if layer.startswith("."):  # namespace = 目录扫描物非白名单 (design.md §2), 仅拒隐藏目录
                raise SkeinError(f"目标路径非法: {target} (需 <namespace>/<category>/<topic>.md)")
            for s in srcs:
                sp = self.root / s
                if not sp.exists():
                    raise SkeinError(f"源文件不存在: {s}")
                txt = sp.read_text()
                meta = _frontmatter(txt)
                # 一个源文件 = 一条规则: 标题取 frontmatter title, 整篇正文降级为 `###` 子节
                # (源文件内的 `## 铁律`/`## 反例表` 是规则的组成部分, 不是独立规则)
                if not dry:
                    self._append_rule(t, layer, cat, t.stem,
                                      str(meta.get("title", "")) or sp.stem,
                                      _clean_body(_strip_frontmatter(txt)),
                                      str(meta.get("keywords", "")),
                                      str(meta.get("status", "active")))
                if sp != t:  # 源即目标 (原地升格) → 不归档自己
                    srcs_all.append(sp)
            print(f"{'[dry] ' if dry else ''}{target} ← {len(srcs)} 个源文件")
        if dry:
            print(f"[dry-run] 共 {len(plan)} 个主题文件 / {len(srcs_all)} 个源文件, 未落盘")
            return
        moved = self._archive_batch(srcs_all, {f: ("restructure", "合并进主题文件") for f in srcs_all})
        self._reindex_all()
        print(f"已重构: {len(plan)} 个主题文件, 源 {moved} 个已归档 (可 restore 回滚)")
