---
title: cortex lint 加 path-lang-mismatch — 文件夹/文件名按 vault lang 校验 (专名豁免)
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

`_meta/version.json:lang` 设定 vault 主语言 (zh-CN / en / ja), `locales/<lang>.yml:dirs` 已映射顶层目录名 (zh-CN: `知识库/项目/...`, en: `kb/projects/...`)。

但**仅顶层目录**走 locale, 子级目录 / 文件名命名**不强制对齐 lang**:
- zh-CN vault: `知识库/项目/<repo>/architecture.md` (英文文件名混入)
- en vault: `kb/projects/<repo>/架构.md` (中文文件名混入)

要求 lint 加规则检测 path segment lang 一致性, **专名豁免** (项目名 / repo 名 / 已有英文专有词)。

# 设计

## 1. 新 lint 规则 `path-lang-mismatch`

| severity | autofix |
|---|---|
| warn | ✗ (人工 rename, AI 提议 cortex-refactor) |

### 1.1 检测逻辑

对 `知识库/**/*.md` 与 `知识库/**/` 目录:

1. 取 vault lang = `_meta/version.json:.lang` (默认 zh-CN)
2. 对每个 path segment (排除 vault root + 排除豁免段) 判:
   - **zh-CN**: segment 应主要含中文字符 (CJK Unicode 范围 `一-龥`), 占比 ≥ 30%
   - **en**: segment 应主要含 ASCII (Latin + 数字 + 连字符), 不含 CJK
   - **ja**: 含 Hiragana/Katakana/Kanji 之一
3. 不符 → flag `path-lang-mismatch`

### 1.2 豁免清单 (强制不检测)

| 豁免段 | 例 |
|---|---|
| host segment | `github.com`, `gitlab.com`, `gitlab.starpago.com` |
| org segment | `lazygophers`, `microsoft`, `gofiber` |
| repo segment | `ccplugin`, `go-zero`, `react` |
| 项目内子目录三段以下 (host/org/repo) | `知识库/项目/<host>/<org>/<repo>/` 的前 3 段 |
| 文件名 ASCII 专名 stem | `README.md`, `LICENSE.md`, `CHANGELOG.md`, `pyproject.toml`, `tsconfig.json` |
| frontmatter `path_lang_exempt: true` 标记 | 用户手动豁免单文件 |
| `.obsidian/` / `.trash/` / `.git/` 等隐藏 | 永远豁免 |
| `_meta/` / `_templates/` / `_assets/` / `locales/` | 基础设施 |

### 1.3 实现位置

`scripts/lint/run.py` 加 `_check_path_lang_mismatch(vault, lang, whitelist)`:

```python
_CJK_RE = re.compile(r'[一-龥]')
_ASCII_NAME_RE = re.compile(r'^[A-Za-z0-9._\-]+$')

def _check_path_lang_mismatch(vault, lang, whitelist):
    findings = []
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        parts = rel.parts
        # exempt: 项目/<host>/<org>/<repo>/ 前 4 段不检 (项目本身 + host+org+repo)
        if len(parts) >= 4 and parts[0] == "知识库" and parts[1] == "项目":
            parts = parts[4:]  # skip 项目/host/org/repo
        elif parts[0] in {"_meta", "_templates", "_assets", "locales", ".obsidian", ".trash", ".git"}:
            continue
        # check each segment
        for seg in parts:
            if _is_exempt_filename(seg) or _is_exempt_path(rel):
                continue
            if lang.startswith("zh"):
                if not _CJK_RE.search(seg) and _ASCII_NAME_RE.match(seg):
                    findings.append({"path": str(rel), "segment": seg, "lang": lang, ...})
                    break
            elif lang == "en":
                if _CJK_RE.search(seg):
                    findings.append(...)
                    break
            # ja...
    return findings
```

`_is_exempt_filename`: stem in {README, LICENSE, CHANGELOG, CONTRIBUTING, pyproject, package, Cargo, go, tsconfig, ...}

`_is_exempt_path`: frontmatter 含 `path_lang_exempt: true`

### 1.4 输出格式

```json
{
  "rule": "path-lang-mismatch",
  "severity": "warn",
  "file": "知识库/项目/<repo>/architecture.md",
  "line": 0,
  "msg": "文件名 'architecture.md' 不符 lang=zh-CN (应中文, 建议 '架构.md'); 项目名/repo 名/ASCII 专名可加 path_lang_exempt: true 豁免",
  "fixable": false,
  "segment": "architecture.md",
  "vault_lang": "zh-CN"
}
```

## 2. SKILL.md (cortex-lint) 同步

§3 规则表加第 18 条 `path-lang-mismatch warn ✗`, 描述: "vault path segment 不符 vault.lang, 豁免: host/org/repo + ASCII 专名 + frontmatter path_lang_exempt"。

## 3. ingest skill / save skill 同步

`skills/cortex-ingest/SKILL.md` §3 frontmatter schema 加可选字段 `path_lang_exempt: <bool>` (默认 false, 仅专名页填 true)。

`skills/cortex-save/SKILL.md` 路径计算时, 若 lang=zh-CN 应用中文 stem (架构 vs architecture), 已知专名 (项目名 / repo 名 / 配置名) 保留 ASCII。

## 4. docs/Lint 规则.md 加 18 条说明

# 验收

1. `scripts/lint/run.py` 加 `_check_path_lang_mismatch` 函数
2. `scripts/lint/rules.json` 加 rule 18 `path-lang-mismatch`
3. `scripts/lint/schemas.py` 不变 (这是单文件规则)
4. 新 unit test `tests/python/test_lint_path_lang.py` (≥6 case: zh path 中文 OK / zh path 英 stem flag / en path 中 flag / host/org/repo 豁免 / README 豁免 / frontmatter exempt)
5. SKILL.md / docs / ingest / save 同步
6. GLM 自检识别 "path-lang-mismatch 规则 + 豁免 host/org/repo + ASCII 专名"
7. pytest 314 + N (新 case) pass

# 不做

- 不 autofix (rename 涉及 wikilink 联动, 走 cortex-refactor rename)
- 不强制存量改名 (老 vault 现有英文 stem 在 zh vault 内将批量 warn — 接受)
- 不检测 `记忆/L0-L4/**` (内部 URI 命名固定)

# 风险

- zh-CN vault 历史存量英文 stem 大量 warn → 接受 (lint warn 非 error, 不阻塞)
- 误判 (zh-CN segment 含纯英文专名如 `知识库/项目/github.com/lazygophers/ccplugin/Bases配置.md`) → ASCII 占比阈值 < 70% 时不 flag
- 豁免清单不完整 → frontmatter `path_lang_exempt` 兜底
