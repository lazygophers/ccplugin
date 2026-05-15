# cortex 强制评分 frontmatter — 知识库 4 + 记忆 2 字段 + digest/refresh 联动更新

## Goal

cortex 当前 frontmatter 仅 score (1-5 整数) + maturity 反映文档质量, 缺**可信度 / 源可信度 / 重要程度**等多维评分。本任务:

1. 知识库 frontmatter 强制 4 评分字段
2. 记忆 frontmatter 强制 2 评分字段
3. **统一 0.0-10.0 浮点** (用户修正, 含原有 score 迁移)
4. AI 落档时自评初值 (ingest_remote / save / digest 都出)
5. digest 跑 evolution 双路调 (使用频率 + 用户反馈)
6. refresh_projects 跑增量时, 内容变 → maturity 重评, score+confidence 保持
7. lint rule 21 强制校验 (warn 级, 渐进迁移)

## What I already know

### 现有 frontmatter schema

`skills/cortex-ingest/references/extract.md §3` 已定义:
- type / title / desc / created / updated / tags (≥10) / source_url / version / when_to_read
- **score: 1-5 整数** (要迁移到 0-10 浮点)
- **maturity: draft|review|stable|deprecated** (保留)

`skills/cortex-save/SKILL.md` 落档逻辑写入。

### 记忆现状

`记忆/L0-核心/` `L1-长期/` `L2-中期/` `L3-短期/` `L4-流水账/` 五层, frontmatter schema 不统一。L0 / L1 重要内容**当前无 importance / confidence 字段**。

`scripts/cli/memory.py` 现有 memory CRUD CLI (URI 寻址)。

### evolution patterns (上批已加)

`记忆/L0-核心/patterns.md` 已用 confidence (0-1) + applications。本任务 confidence 全统一 0-10, 旧 0-1 也要迁移。

## Decision (ADR-lite)

**Context**: 用户 4 AskUserQuestion 锁定 + 关键修正 "0-10 浮点数"。

**Decision**:
- D1 字段 schema:
  - **知识库强制 4**: `score` (0.0-10.0) / `confidence` (0.0-10.0) / `source_credibility` (0.0-10.0) / `maturity` (enum, 保留)
  - **记忆强制 2**: `importance` (0.0-10.0) / `confidence` (0.0-10.0)
- D2 范围: **0.0-10.0 浮点**, 含原 score (1-5) 迁移 × 2.0
- D3 初值: **AI 自评** (ingest_remote / save / digest 落档时按启发式)
- D4 digest 双路:
  - 使用信号: sessions/jsonl 召回次数 + vault wikilink 反向引用次数 → importance ↑
  - 反馈信号: 用户纠正语 (含"不对/错了" 等) → confidence ↓; 用户加强/引用 → confidence ↑
- D5 refresh: 内容 hash 变 → maturity 重评 (Bayesian: stable→review→draft 链), score/confidence 保持

**Consequences**:
- 现有 vault 文件**全缺**新字段 → lint warn (非 fail) 渐进迁移, autofix 加 stub `confidence: 0.0 # TODO AI 自评`
- evolution patterns confidence 0-1 → 0-10 也迁 (× 10)
- score 1-5 → 0-10 (× 2.0) 一次性 migration script

## Requirements

### R1: SKILL/references schema 更新

#### F1.1 `skills/cortex-ingest/references/extract.md` §3 重写

```yaml
---
# 旧字段 (类型保留, score 范围改)
type: <concept|domain|log>
title: <人类可读标题>
desc: <1-3 句>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
tags: [...]  # ≥ 10
source_url: <URL>
version: <sha/tag/version>
when_to_read: <触发描述>
maturity: <draft|review|stable|deprecated>

# 新字段 (强制 4, 0.0-10.0 浮点)
score: 7.5             # 内容质量 (覆盖度 + 深度 + 准确性 综合)
confidence: 8.0        # 内容可信度 (AI 对自己写的有多确定)
source_credibility: 9.0 # 源可信度 (官方 doc > 学术 > 知名博客 > 个人 > 匿名)
---
```

加"AI 自评启发式"小节:

| 字段 | 计算源 | 范围 |
|---|---|---|
| score | 6 类抽取覆盖率 (API/配置/错误码/测试/功能/常量) | 0=无覆盖 / 5=半数 / 10=全覆盖 |
| confidence | tags 完整性 + when_to_read 明确性 + 内部 wikilink ≥ 5 | 0=骨架 / 5=合理 / 10=丰满 |
| source_credibility | host 白名单匹配 (官方 doc ≥ 9, arxiv ≥ 8, github ≥ 7, 个人博客 ≥ 5, 匿名 ≤ 4) | 硬编码 host_credibility_table |
| maturity | 内容变更频率 (refresh hash 变次数 ÷ 时间窗口) | draft/review/stable/deprecated |

#### F1.2 `skills/cortex-save/SKILL.md` 加强制 frontmatter

引用 references/extract.md §3 同表, 加 §"评分字段 (强制)"小节。

#### F1.3 新 `skills/cortex-memory/references/scoring.md`

记忆评分规范:

```yaml
---
# 强制 2 字段 (0.0-10.0 浮点)
importance: 8.0   # 重要程度 (核心约束/价值观 = 10, 流水账 = 1-3)
confidence: 7.0   # 可信度 (用户明确肯定 = 10, AI 推测 = 4-6, 失败 episode = 0-3)
---
```

按 L0-L4 层默认范围:
- L0 核心: importance ≥ 8, confidence ≥ 9
- L1 长期: importance ≥ 6, confidence ≥ 7
- L2 中期: importance ≥ 4, confidence ≥ 5
- L3 短期: importance ≥ 2, confidence ≥ 3
- L4 流水账: importance ≤ 3, confidence 不限

### R2: lint rule 21 `frontmatter-required-scores`

#### F2.1 `scripts/lint/rules.json` 加规则

```json
{
  "id": "frontmatter-required-scores",
  "name": "frontmatter-required-scores",
  "severity": "warn",
  "autofix": true,
  "description": "知识库 md 必含 score/confidence/source_credibility/maturity 4 字段, 记忆 md 必含 importance/confidence 2 字段, 全 0.0-10.0 浮点 (maturity enum)"
}
```

#### F2.2 `scripts/lint/run.py` 加 `check_frontmatter_required_scores`

逻辑:
- `知识库/**/*.md`: 验 4 字段存在 + 类型 (float 0-10) + maturity in 4 enum
- `记忆/**/*.md`: 验 2 字段
- 缺字段 → warn + autofix 加 stub:
  ```yaml
  score: 0.0  # TODO AI 自评
  confidence: 0.0  # TODO AI 自评
  source_credibility: 0.0  # TODO AI 自评
  maturity: draft
  ```
- 类型错 (整数 / 字符串) → warn + autofix 转 float
- 范围越界 (< 0 / > 10) → warn + autofix clamp

#### F2.3 测试 `tests/python/test_frontmatter_scores_lint.py`

≥ 12 case:
- 知识库 .md 4 字段全 → ok
- 知识库缺 score → warn + autofix
- 知识库缺 confidence → warn + autofix
- 知识库缺 source_credibility → warn + autofix
- 知识库 score=10 → ok (boundary)
- 知识库 score=10.5 → autofix clamp 10
- 知识库 score="high" → autofix 0.0
- 知识库 score=5 (整数) → autofix 5.0
- 记忆 importance 缺 → warn
- 记忆 confidence 缺 → warn
- maturity="bad-enum" → warn + autofix "draft"
- 非 知识库/记忆 路径 (仪表盘 / 收件箱 / 日记) → skip

### R3: ingest_remote / save AI 自评写入

#### F3.1 `scripts/cli/lib/remote.py` 加 `_compute_initial_scores`

```python
_HOST_CREDIBILITY = {
    "anthropic.com": 10.0, "openai.com": 10.0,
    "react.dev": 9.5, "docs.python.org": 9.5,
    "arxiv.org": 8.5, "github.com": 7.5, "gitlab.com": 7.5,
    "stackoverflow.com": 7.0, "medium.com": 5.0,
}

def compute_initial_scores(source_type, host, coverage_ratio, tag_count, wikilink_count):
    """落档时计算 4 评分字段初值. coverage_ratio ∈ [0,1] (6 类抽取命中数 / 6)."""
    score = round(coverage_ratio * 10, 1)
    confidence = min(10.0, (tag_count / 10) * 5 + (wikilink_count / 5) * 5)
    source_credibility = _HOST_CREDIBILITY.get(host, 5.0)
    maturity = "draft" if score < 5 else ("review" if score < 8 else "stable")
    return {"score": score, "confidence": confidence, "source_credibility": source_credibility, "maturity": maturity}
```

ingest_git / ingest_website 落每页时调 `compute_initial_scores()` 写入 frontmatter。

#### F3.2 `scripts/cli/save.py` 同步

save.py 落档时类似计算:
- score: 由 body 长度 + heading 数 + code block 数推
- confidence: AI 调用 save 时显式 --confidence=8.5 可覆盖
- source_credibility: 来自 --source-url 解析 host
- maturity: 由 kind 推 (reflection=draft, log=stable)

加 CLI flag: `--score=N` / `--confidence=N` / `--source-credibility=N` / `--maturity=draft|review|stable|deprecated` (override AI 自评)。

### R4: digest 双路评分更新

#### F4.1 `scripts/cli/lib/evolution.py` 加 `_update_scores` 函数

```python
def update_doc_scores(doc_path, sessions_dir, vault):
    """digest 跑时调, 双路更新文档 frontmatter 评分.
    
    使用信号 (importance ↑):
    - 扫 sessions/jsonl 最近 7 天, count doc_path 被 wikilink/搜 命中次数 = N
    - 扫 vault 反向 wikilink, count = M
    - importance_delta = log(N + M + 1) / log(10) ∈ [0, ~2]
    - new_importance = clamp(old + importance_delta - 0.1, 0, 10)
      (每周 -0.1 自然衰减)
    
    反馈信号 (confidence ↑↓):
    - 扫 sessions 用户消息含纠正语 ("不对/错了") + 该 doc_path → confidence -= 1.0
    - 用户加强语 ("对的/正确/很好") + 该 doc_path → confidence += 0.5
    """
```

`scripts/cli/digest.py evolution` 子命令加新 stage: `--update-scores` 默认开。

#### F4.2 patterns.md schema 升级

evolution patterns confidence 从 0-1 → 0-10 (× 10), 加 `importance` 字段:
- pattern applications=3+ → importance 5+
- 高频 pattern (applications=10+) → importance 8+

migration 一次性脚本: `scripts/migrate/migrate_patterns_to_v2.py` (一次性, 跑后归档)。

### R5: refresh_projects 内容变 → maturity 重评

#### F5.1 `scripts/cli/refresh_projects.py` 加 `_revalue_maturity`

```python
def revalue_maturity(old_maturity, hash_change_count, days_since_last_change):
    """内容 hash 变 → maturity 重评. 不动 score/confidence (D5 锁定).
    
    规则:
    - hash 变 1 次 且 旧 maturity=stable → review (回退到 review)
    - hash 变 ≥ 2 次 且 < 30 天 → draft (频繁变动 = 不成熟)
    - 长期不变 (≥ 90 天) → stable
    - 极少访问 + 长期不变 (≥ 180 天) → deprecated 候选 (人工确认)
    """
```

refresh_website / refresh_git 调 `revalue_maturity()` patch frontmatter。

### R6: 一次性 migration

#### F6.1 `scripts/migrate/migrate_scores_to_v2.py` (一次性, 跑后归档)

- 扫 vault 内全部 .md
- 旧 score 1-5 整数 → score 0-10 浮点 × 2.0
- 旧 evolution patterns.md confidence 0-1 → × 10
- 缺字段 → 加 stub `0.0 # TODO AI 自评`
- 输出 migration report (改 N 文件, 加 M 字段)
- backup vault → tmp/cortex-migration-backup-<YYYYMMDD>.tar.gz

#### F6.2 wrapper `scripts/migrate.sh`

类 install_cron.sh / refresh_projects.sh 风格, 一次性 wrapper:
```bash
bash ~/.cortex/scripts/migrate.sh --to=v2 [--dry-run]
```

### R7: docs / AGENT.md / memory 同步

- `docs/Lint 规则.md`: rule 21 描述
- `docs/快速上手.md`: migration 用例 + 评分字段说明
- `docs/故障排查.md`: 评分缺失 / 范围越界 / 迁移失败 排查
- `AGENT.md`: §资产 lint 20 → 21, 加 migration script 说明
- `.claude/memory/cortex-plugin-2026-05-13.md`:
  - Lint 20 → 21
  - 加 §P8 节: 强制评分字段 schema + digest 双路 + refresh 重评 + migration

## Acceptance Criteria

- [ ] references/extract.md §3 schema 升级 (4 字段 0-10 浮点)
- [ ] cortex-memory references/scoring.md 新建 (2 字段)
- [ ] lint rule 21 + autofix 加 stub
- [ ] ingest_remote / save 写入 4 字段初值 (AI 自评启发式)
- [ ] digest evolution 双路更新 importance/confidence
- [ ] refresh_projects 重评 maturity
- [ ] 一次性 migration script + wrapper
- [ ] evolution patterns.md confidence 0-1 → 0-10 migration
- [ ] pytest 基线 402 → ≥ 420 (≥ +18 新测试)
- [ ] ruff clean
- [ ] docs/memory/AGENT.md 同步
- [ ] AI 质量检查 cortex-ingest / cortex-save SKILL 仍正确识别

## Definition of Done

- pytest 全绿
- ruff clean
- migration --dry-run 在真 vault 跑一遍验证无破坏
- lint --rule frontmatter-required-scores 真 vault 跑检出缺字段
- git commit (拆 6 commits 按 PR)

## Out of Scope

- 不动用户已写的 score 值 (除 1-5 → 0-10 × 2.0 mechanical migration)
- 不做 AI 自评算法 ML 化 (启发式 host 表 + coverage_ratio 足够)
- 不破坏 402 pytest 基线 / 20 lint rule (变 21)
- 不动 ingest_remote/refresh_projects 上批 PR 实现 (仅扩展 score 写入)
- 不实现 deprecated 自动归档 (R5 仅推荐 candidate, 人工确认)

## Technical Notes

- AI 自评启发式权威: `skills/cortex-ingest/references/extract.md §3 评分字段`
- host_credibility table: `scripts/cli/lib/remote.py:_HOST_CREDIBILITY` (公共字典)
- migration backup: `tmp/cortex-migration-backup-<YYYYMMDD>.tar.gz` 用户手动恢复
- 旧值兼容: lint autofix 仅加 stub, 不强制 AI 重评; 用户主动调 save/refactor 实际填值

## Implementation Plan (6 PR 拆分)

| PR | 范围 |
|---|---|
| PR1 | SKILL/references schema 升级 (extract.md + 新 scoring.md, 文档 only) |
| PR2 | lint rule 21 + autofix stub + 测试 |
| PR3 | ingest_remote / save 写入 4 字段 + AI 自评启发式 (lib/remote.py + save.py) |
| PR4 | digest 双路更新 (lib/evolution.py + 测试) |
| PR5 | refresh_projects maturity 重评 (refresh_projects.py + 测试) |
| PR6 | migration script + wrapper + docs/memory/AGENT 同步 |
