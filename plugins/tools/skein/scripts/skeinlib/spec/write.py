"""sediment 写盘 — 规则作为一个 `## <标题>` 章节**追加**进主题文件。

粒度: 目录 = 类目, 文件 = 主题, 文件内 `## <标题>` = 一条规则。同主题规则必须并入同一文件
(禁一规则一文件, 否则索引膨胀而召回质量不升)。frontmatter 只写 title/category/keywords/
status/inclusion (+ fileMatch 的 globs、可选 anchors), **不写时间字段** —— 新旧判定一律走
文件系统 mtime, 存进 frontmatter 只会与事实漂移。
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast
import re

from pydantic import BaseModel, Field

from skeinlib.utils.errors import SkeinError
from skeinlib.spec.text import _frontmatter, _slug, _strip_frontmatter, _sections


class AnchorHit(BaseModel):
    """finish-candidates anchor 命中。"""
    file: str = Field(description="变更文件")
    anchor: str = Field(description="命中的 anchor")
    rule: str = Field(description="product 规则 ID")


class KeywordCandidate(BaseModel):
    """finish-candidates 关键词召回候选。"""
    rule: str = Field(description="规则 ID")
    title: str = Field(description="规则标题")
    keywords: str = Field(description="规则关键词")
    matched_keywords: list[str] = Field(description="命中的关键词")


class FinishCandidatesResult(BaseModel):
    """finish-candidates 输出结构。"""
    tid: str
    files: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    anchor_hits: list[AnchorHit] = Field(default_factory=list)
    weak_candidates: list[KeywordCandidate] = Field(default_factory=list)
    has_candidates: bool = False
    message: str | None = None
    suggestion: str | None = None

class WriteMixin:
    # 仅供 mypy 用的属性声明: root/layer_dir/_scan_namespaces/_rules/_rule_files 由兄弟类
    # SpecBase 提供, _reindex_all 由兄弟 mixin IndexMixin 提供 (组装成 Spec 时混入)。
    # TYPE_CHECKING 块运行时永不执行, 零行为改动, 只消除单看本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        root: Path
        def layer_dir(self, layer: str) -> Path: ...
        def _scan_namespaces(self) -> list[str]: ...
        def _rules(self, layer: str) -> list[tuple[Path, str, str]]: ...
        def _rule_files(self, layer: str) -> list[Path]: ...
        def _reindex_all(self) -> dict[str, dict[str, int]]: ...

    # ---- namespace/inclusion 取参 (sediment/archive 共用) ----
    def _require_namespace(self, a: argparse.Namespace, *, with_inclusion: bool) -> tuple[str, Optional[str]]:
        """返回 (namespace, inclusion|None)。namespace 是自由字符串 (非白名单, design.md §2)。

        曾有个 `--layer` 废弃通道把旧的 core/recall/external 三值映射到 (namespace, inclusion),
        已整条删除 —— 两套词汇并存期间光是内部互译 shim 就漂移出过多处 bug (最后一次是看板 spec
        树对新 namespace 全盲)。现在只有一套: namespace × inclusion。
        """
        namespace = cast(Optional[str], getattr(a, "namespace", None))
        inclusion = cast(Optional[str], getattr(a, "inclusion", None)) if with_inclusion else None
        if namespace is None:
            raise SkeinError("需要 --namespace (自由字符串, 常见 rules/product/map/external)")
        return namespace, (inclusion or "auto") if with_inclusion else None
    # ---- sediment (写盘: 规则作为一个章节追加进主题文件, 判定门通过后自动调用) ----
    def sediment(self, a: argparse.Namespace) -> None:
        namespace, inclusion_opt = self._require_namespace(a, with_inclusion=True)
        inclusion = cast(str, inclusion_opt)
        title = cast(str, a.title)
        keywords = cast(Optional[str], getattr(a, "keywords", None)) or ""
        status = cast(Optional[str], getattr(a, "status", None)) or "active"
        body_file = cast(Optional[str], getattr(a, "body_file", None))
        if not body_file:
            raise SkeinError("--body-file 必填: 正文只认文件, 不收命令行内联 — "
                             "先把规则正文写进一个 .md 文件, 再 `skein-spec sediment ... --body-file <该文件>`")
        cat = cast(Optional[str], getattr(a, "category", None)) or "misc"
        globs = cast(Optional[str], getattr(a, "globs", None))
        anchors = cast(Optional[str], getattr(a, "anchors", None))
        # --topic 缺省 → 归入类目同名主题文件 (调用方应按语义指定主题, 免所有规则挤一个文件)
        topic = _slug(cast(Optional[str], getattr(a, "topic", None)) or cat)
        d = self.layer_dir(namespace) / cat
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{topic}.md"
        body = (Path(body_file).read_text() if body_file else "").strip()
        self._append_rule(f, namespace, cat, topic, title, body, keywords, status,
                          inclusion, globs, anchors)
        self._reindex_all()
        print(f"已沉淀 → {f.relative_to(self.root).as_posix()}#{title}")
    def _append_rule(self, f: Path, namespace: str, cat: str, topic: str, title: str,
                     body: str, keywords: str, status: str,
                     inclusion: str = "auto", globs: Optional[str] = None,
                     anchors: Optional[str] = None) -> None:
        """把一条规则作为 `## <title>` 章节追加进主题文件 (不存在则建)。

        frontmatter: title/category/keywords/status 五字段 + inclusion (显式加载策略) +
        legacy `layer` 字段 (core/recall 二值, 由 inclusion 反推, 供旧代码路径 `_inclusion()`
        fallback / `degrade()` 兼容读取, s6 迁移完再删) + 可选 globs/anchors (fileMatch 用)。"""
        old_body, kws, st = "", [k.strip() for k in keywords.split(",") if k.strip()], status
        old_globs, old_anchors = globs, anchors
        if f.exists():
            txt = f.read_text()
            meta = _frontmatter(txt)
            old_body = _strip_frontmatter(txt).strip()
            kws = list(dict.fromkeys([k.strip() for k in str(meta.get("keywords", "")).split(",")
                                      if k.strip()] + kws))
            # ponytail: status 是文件级 (主题级) 字段 — 追加时只在显式非 active 时覆盖;
            # 单条规则要独立 status → 拆到自己的主题文件。
            st = status if status != "active" else str(meta.get("status", "active"))
            old_globs = globs if globs is not None else (str(meta.get("globs", "")) or None)
            old_anchors = anchors if anchors is not None else (str(meta.get("anchors", "")) or None)
        extra = ""
        if old_globs:
            extra += f"globs: {old_globs}\n"
        if old_anchors:
            extra += f"anchors: {old_anchors}\n"
        f.write_text(
            "---\n"
            f"title: {topic}\n"
            f"category: {cat}\n"
            f"keywords: [{','.join(kws)}]\n"
            f"status: {st}\n"
            f"inclusion: {inclusion}\n"
            + extra +
            "---\n\n"
            + (old_body + "\n\n" if old_body else "")
            + f"## {title}\n\n{body}\n")
    # ---- list ----
    def list_(self, a: argparse.Namespace) -> None:
        ns_opt = cast(Optional[str], getattr(a, "namespace", None))
        # 目录扫描而非常量白名单 — 与 reindex/maintain 一致, 否则手建 namespace 不进 list (design.md §2)
        for ns in ([ns_opt] if ns_opt else self._scan_namespaces()):
            d = self.layer_dir(ns)
            rules = [f"{f.relative_to(d).as_posix()}#{t}" for f, t, _ in self._rules(ns)]
            print(f"[{ns}] {len(rules)} 条规则 / {len(self._rule_files(ns))} 个主题: "
                  f"{', '.join(rules) or '-'}")

    # ---- amend (改写既有章节正文, 其余章节与 frontmatter 逐字不动) ----
    def amend(self, a: argparse.Namespace) -> None:
        """改写既有章节正文, 其余章节与 frontmatter 逐字不动; 改前 archive 旧版。

        验收要求:
        1. 改写只动目标章节
        2. restore 可取回改前内容
        3. 章节不存在报错且列现有章节名
        4. rename-section 反链跟随不断链
        5. amend 后 index/FTS/backlinks 已同步
        """
        from skeinlib.spec.model import now

        topic_path = cast(str, a.topic)
        section_name = cast(str, a.section)
        body_file = cast(str, a.body_file)
        new_section_name_opt = cast(Optional[str], getattr(a, "rename_section", None))

        # 解析 topic 路径: <ns>/<cat>/<topic>
        parts = topic_path.split("/")
        if len(parts) != 3:
            raise SkeinError(f"无效的 --topic 格式: {topic_path} (应为 <ns>/<cat>/<topic>)")
        namespace, cat, topic = parts

        # 构建文件路径
        f = self.layer_dir(namespace) / cat / f"{topic}.md"
        if not f.exists():
            raise SkeinError(f"主题文件不存在: {f.relative_to(self.root)}")

        # 读取当前文件内容
        txt = f.read_text()
        meta = _frontmatter(txt)
        sections = _sections(txt)

        # 检查目标章节是否存在
        section_titles = [title for title, _ in sections]
        if section_name not in section_titles:
            raise SkeinError(
                f"章节不存在: {section_name}\n"
                f"现有章节: {', '.join(section_titles) or '(无章节)'}"
            )

        # 读取新正文
        new_body = Path(body_file).read_text().strip()

        # amend 前自动 archive 旧版到 .archive/<ts>/
        ts = str(now())
        archive_dir = self.root / ".archive" / ts / f.relative_to(self.root)
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt)  # 确保原内容完整
        f.rename(archive_dir)  # 移到归档

        # 如果要改名, 先更新反链
        if new_section_name_opt:
            self._update_backlinks_for_rename(namespace, cat, topic, section_name, new_section_name_opt)

        # 构建新的文件内容
        new_sections = []
        for title, content in sections:
            if title == section_name:
                # 替换目标章节
                final_title = new_section_name_opt or section_name
                new_sections.append((final_title, new_body))
            else:
                # 保留其他章节不变
                new_sections.append((title, content))

        # 重新组装文件内容 (保持 frontmatter 不变)
        new_body_text = "\n\n".join(
            f"## {title}\n\n{content}" for title, content in new_sections if content.strip()
        )

        # 重建 frontmatter
        frontmatter = self._rebuild_frontmatter(meta)
        new_content = frontmatter + "\n\n" + new_body_text if frontmatter else new_body_text

        # 写入新文件
        f.write_text(new_content)

        # 自动 reindex
        self._reindex_all()

        if new_section_name_opt:
            print(f"已改写章节: {section_name} → {new_section_name_opt} ({f.relative_to(self.root).as_posix()})")
        else:
            print(f"已改写章节: {section_name} ({f.relative_to(self.root).as_posix()})")
        print(f"归档旧版: {archive_dir.relative_to(self.root).as_posix()}")

    def _rebuild_frontmatter(self, meta: dict[str, str]) -> str:
        """重建 frontmatter, 保持字段顺序和格式。"""
        if not meta:
            return ""

        lines = ["---"]
        # 保持字段顺序
        for key in ["title", "category", "keywords", "status", "inclusion", "globs", "anchors"]:
            if key in meta:
                value = meta[key]
                if key == "keywords" and not value.startswith("["):
                    value = f"[{value}]"
                lines.append(f"{key}: {value}")

        # 添加其他字段
        for key, value in meta.items():
            if key not in ["title", "category", "keywords", "status", "inclusion", "globs", "anchors"]:
                lines.append(f"{key}: {value}")

        lines.append("---")
        return "\n".join(lines)

    def _update_backlinks_for_rename(self, namespace: str, cat: str,
                                    topic: str, old_section: str, new_section: str) -> None:
        """更新反链中引用了改名的章节的 wikilink。

        搜索所有文件中的 [[<ns>/<cat>/<topic>#<old_section>|别名]] 形式的 wikilink,
        替换为 [[<ns>/<cat>/<topic>#<new_section>|别名]]。
        """
        from skeinlib.spec.text import _link_target

        target_link = f"{topic}#{old_section}"

        # 搜索所有可能引用这个章节的文件
        for ns in self._scan_namespaces():
            for f in self._rule_files(ns):
                try:
                    txt = f.read_text()
                    # 查找所有 wikilink
                    pattern = r'\[\[([^\]]+)\]\]'
                    links = re.findall(pattern, txt)

                    modified = False
                    for link in links:
                        target = _link_target(link)
                        if target == target_link:
                            # 替换 wikilink
                            old_wikilink = f"[[{link}]]"
                            # 保留别名部分（如果有）
                            if "|" in link:
                                alias = link.split("|")[1]
                                new_wikilink = f"[[{namespace}/{cat}/{topic}#{new_section}|{alias}]]"
                            else:
                                new_wikilink = f"[[{namespace}/{cat}/{topic}#{new_section}]]"
                            txt = txt.replace(old_wikilink, new_wikilink)
                            modified = True

                    if modified:
                        f.write_text(txt)
                        print(f"更新反链: {f.relative_to(self.root).as_posix()}")
                except Exception:
                    # 忽略读取错误, 继续处理其他文件
                    pass

    # ---- finish-candidates (finish 回写候选反查) ----
    def finish_candidates(self, a: argparse.Namespace) -> None:
        """为 task 生成候选 product wiki 页 (三路降级: anchors反查→TaskSpec关键词recall→皆无建议新建)。

        验收要求:
        1. anchors 命中路输出带命中 anchor
        2. 关键词路标注弱候选
        3. 皆无命中如实报建议新建且不硬凑
        4. 缺省 JSON 机器可读, --show 人读文本
        5. 文件列表可参数注入(测试无需真 git 仓)
        """
        import json
        import subprocess

        tid = cast(str, a.tid)
        use_json = not cast(bool, getattr(a, "show", False))  # 缺省 JSON; --show 走人读文本
        files_param = cast(Optional[str], getattr(a, "files", None))

        # 构建任务目录路径
        task_dir = self.root.parent / "task" / tid
        if not task_dir.exists():
            raise SkeinError(f"任务目录不存在: {task_dir}")

        # 关键词来源: task.json 的 TaskSpec 字段 (desc/边界/验收) 拼接文本
        keywords: list[str] = []
        task_json = task_dir / "task.json"
        if task_json.exists():
            import json as _json
            data = _json.loads(task_json.read_text())
            b = data.get("boundary") or {}
            spec_text = " ".join([data.get("desc") or "", *(b.get("should") or []),
                                  *(b.get("should_not") or []), *(data.get("acceptance") or [])])
            keywords = self._extract_keywords(spec_text)

        # 获取文件列表
        if files_param:
            # 测试模式：从参数注入
            changed_files = [f.strip() for f in files_param.split(",") if f.strip()]
        else:
            # 生产模式：从 git diff 获取
            repo_root = self.root.parent.parent

            # 优先检查工作目录的未暂存变更
            proc = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True, text=True, cwd=repo_root
            )
            working_files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]

            # 检查已暂存但未提交的变更
            proc = subprocess.run(
                ["git", "diff", "--staged", "--name-only"],
                capture_output=True, text=True, cwd=repo_root
            )
            staged_files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]

            # 合并工作目录和暂存区的变更（去重）
            changed_files = sorted(set(working_files + staged_files))

            # 如果没有变更，尝试与上次提交比较
            if not changed_files:
                proc = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                    capture_output=True, text=True, cwd=repo_root
                )
                changed_files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]

        result: FinishCandidatesResult
        if not changed_files:
            result = FinishCandidatesResult(tid=tid, message="无文件变更, 无法生成候选")
        else:
            # 第一路: anchors 反查 (高优先级)
            anchor_hits = self._reverse_lookup_anchors(changed_files)

            # 第二路: TaskSpec 关键词 recall --src product (弱候选)
            weak_candidates: list[KeywordCandidate] = []
            if keywords and not anchor_hits:
                weak_candidates = self._recall_by_keywords(keywords)

            # 第三路: 皆无则如实报建议新建
            result = FinishCandidatesResult(
                tid=tid,
                files=changed_files,
                keywords=keywords,
                anchor_hits=anchor_hits,
                weak_candidates=weak_candidates,
                has_candidates=bool(anchor_hits or weak_candidates),
            )

            if not anchor_hits and not weak_candidates:
                result.message = "无候选, 可能是新功能域, 建议新建 product wiki 页"
                result.suggestion = f"可用: skein-spec sediment --namespace product --category <类目> --topic <主题> --title <标题> --keywords \"{','.join(keywords)}\" --body-file <正文文件>"

        # 输出结果
        if use_json:
            print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        else:
            self._print_finish_candidates_result(result)

    def _extract_keywords(self, spec_text: str) -> list[str]:
        """从 TaskSpec 拼接文本中提取关键词 (标题/强调/分词)。"""
        import re

        keywords: set[str] = set()

        # 尝试解析 frontmatter 中的 keywords
        frontmatter_match = re.search(r'keywords:\s*\[(.*?)\]', spec_text, re.DOTALL)
        if frontmatter_match:
            kw_str = frontmatter_match.group(1)
            keywords.update(k.strip().strip('"\'') for k in kw_str.split(',') if k.strip())

        if not keywords:
            # 提取强调内容 (**加粗** 或 *斜体*)
            for match in re.finditer(r'[*_*_](.+?)[_*_*_]', spec_text):
                emphasized = match.group(1).strip()
                words = re.findall(r'[\w一-鿿]+', emphasized)
                keywords.update(words)

        return sorted(keywords)

    def _reverse_lookup_anchors(self, changed_files: list[str]) -> list[AnchorHit]:
        """反查 anchors: 从变更文件查找对应的 product wiki 页。"""
        hits: list[AnchorHit] = []

        # 扫描 product namespace 的所有规则
        for rule_file, title, body in self._rules("product"):
            try:
                meta = _frontmatter(rule_file.read_text())
                anchors_str = str(meta.get("anchors", ""))
                if not anchors_str:
                    continue

                anchors = [a.strip() for a in anchors_str.split(",") if a.strip()]

                # 检查是否有变更文件命中这些 anchors
                for changed_file in changed_files:
                    for anchor in anchors:
                        # 简单的路径匹配: 如果 anchor 是 changed_file 的前缀或包含关系
                        if self._path_matches_anchor(changed_file, anchor):
                            rule_id = f"product/{rule_file.parent.name}/{rule_file.stem}.md#{title}"
                            hits.append(AnchorHit(
                                file=changed_file,
                                anchor=anchor,
                                rule=rule_id,
                            ))
                            break  # 一个文件只匹配一次
            except Exception:
                # 忽略解析错误
                pass

        return hits

    def _path_matches_anchor(self, file_path: str, anchor: str) -> bool:
        """判断文件路径是否匹配 anchor。

        支持以下匹配模式:
        1. 完全匹配: file_path == anchor
        2. 前缀匹配: file_path 以 anchor 开头 (anchor 是目录)
        3. 后缀匹配: file_path 以 anchor 结尾 (anchor 是文件名)
        4. 包含匹配: file_path 包含 anchor (anchor 是路径片段)
        """
        # 标准化路径
        file_path = file_path.replace("\\", "/")
        anchor = anchor.replace("\\", "/")

        if file_path == anchor:
            return True
        if file_path.startswith(anchor + "/"):
            return True
        if file_path.endswith("/" + anchor) or file_path.endswith("/" + anchor + ".py"):
            return True
        if "/" + anchor + "/" in "/" + file_path + "/":
            return True

        return False

    def _recall_by_keywords(self, keywords: list[str]) -> list[KeywordCandidate]:
        """基于关键词从 product namespace recall。"""
        if not keywords:
            return []

        candidates: list[KeywordCandidate] = []
        keywords_lower = [k.lower() for k in keywords]

        for rule_file, title, body in self._rules("product"):
            try:
                meta = _frontmatter(rule_file.read_text())
                rule_keywords = str(meta.get("keywords", "")).lower()
                title_lower = title.lower()

                # 检查关键词匹配
                matched_keywords = []
                for kw in keywords_lower:
                    if kw in rule_keywords or kw in title_lower:
                        matched_keywords.append(kw)

                if matched_keywords:
                    rule_id = f"product/{rule_file.parent.name}/{rule_file.stem}.md#{title}"
                    candidates.append(KeywordCandidate(
                        rule=rule_id,
                        title=title,
                        keywords=str(meta.get("keywords", "")),
                        matched_keywords=matched_keywords,
                    ))
            except Exception:
                # 忽略解析错误
                pass

        return candidates

    def _print_finish_candidates_result(self, result: FinishCandidatesResult) -> None:
        """以人类可读格式输出 finish-candidates 结果。"""
        print(f"# Task {result.tid} 的候选 Product Wiki 页")
        print()

        if result.files:
            print(f"涉及文件 ({len(result.files)}):")
            for f in result.files[:10]:  # 只显示前10个
                print(f"  - {f}")
            if len(result.files) > 10:
                print(f"  ... 还有 {len(result.files) - 10} 个文件")
            print()

        if result.keywords:
            print(f"关键词: {', '.join(result.keywords)}")
            print()

        anchor_hits = result.anchor_hits
        weak_candidates = result.weak_candidates

        if anchor_hits:
            print(f"## Anchor 反查命中 ({len(anchor_hits)}) [高优先级]")
            for hit in anchor_hits:
                print(f"  - 文件: {hit.file}")
                print(f"    anchor: {hit.anchor}")
                print(f"    规则: {hit.rule}")
                print()

        if weak_candidates:
            print(f"## 关键词召回候选 ({len(weak_candidates)}) [弱候选]")
            for candidate in weak_candidates:
                print(f"  - 规则: {candidate.rule}")
                print(f"    标题: {candidate.title}")
                print(f"    关键词: {candidate.keywords}")
                print(f"    匹配关键词: {', '.join(candidate.matched_keywords)}")
                print()

        if not anchor_hits and not weak_candidates:
            print("## 无候选")
            print(result.message or "无候选, 可能是新功能域, 建议新建 product wiki 页")
            if result.suggestion:
                print(f"\n建议操作: {result.suggestion}")
        else:
            print(f"总计: {len(anchor_hits) + len(weak_candidates)} 个候选")
