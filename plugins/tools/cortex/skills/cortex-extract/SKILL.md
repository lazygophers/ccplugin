---
name: cortex-extract
description: extract / 提取 / promote / 整理 / 归档 / digest L4-inbox 收件箱条目, 按三轴 (抗遗忘度 / 强度 / 复用面) 路由到 L1-long / L2-mid / L3-short / projects / domains, 默认 dry-run 输出 JSON plan, --apply 落盘 + 增量游标. 用户说 "整理 inbox / 提取记忆 / 归档笔记 / promote / digest" 时使用.
when_to_use: |
  - 用户说 "整理 inbox" / "整理收件箱" / "提取 L4"
  - 用户说 "把临时笔记归档" / "处理 cortex inbox"
  - 用户说 "extract" / "digest" / "promote 记忆"
  - 例行扫描 ~/.cortex/.wiki/memory/L4-inbox/ 或 <repo>/.wiki/memory/L4-inbox/
  - 跨会话沉淀: 把对话留下的临时笔记分级入库
  - 协调 cortex-schema-memory 等级语义 + cortex-schema-knowledge 三模块路径决策
argument-hint: "[--dry-run|--apply] [--target <dir>] [--no-cursor]"
---

# cortex-extract

L4-inbox → L1/L2/L3 + 项目/领域 路由提取器. 默认 dry-run, --apply 才落盘. 三模块目录名采用中文 (项目/领域/脚本); memory/L<n>-<suffix>/ 仍英文.

## 反直觉提醒 (必读)

**默认入口 = L3-short (短期, 最易遗忘)**, 不是 L1. 升级方向 = 抵抗遗忘:

```
L3 短期 ── promote ──▶ L2 中期 ── promote ──▶ L1 长期 ── promote ──▶ L0 核心
(默认入口)              (复用 ≥ 3)             (复用 ≥ 5 + weight ≥ 0.8)   (永远只手动)
```

路径名严格使用 `L0-core / L1-long / L2-mid / L3-short / L4-inbox`. 禁出现 `L1-recent / L1-short / L3-long` 等反写组合.

## 工具入口

```bash
bash plugins/tools/cortex/scripts/extract.sh --help

# Dry-run (默认): 输出 JSON plan, 不落盘
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex

# Apply: 落盘 + 更新游标 + archive 原 inbox 条目
bash plugins/tools/cortex/scripts/extract.sh --apply --target ~/.cortex

# 全量扫 (忽略游标)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## 三轴 (classifier)

| 轴 | 信号源 | 用途 |
| --- | --- | --- |
| 抗遗忘度 | 文件 mtime + frontmatter `created` | 老条目优先 promote; 新条目默认 L3 |
| 强度 | frontmatter `weight` (0-1); 关键词推断 (永远→1.0 / 暂时→0.3 / 默认 0.5) | 决定 L0/L1/L2/L3 候选 |
| 复用面 | inbox 内 token overlap (阈值 3 个相同 token 视为复用) | ≥ 3 提议 L2 promote, ≥ 5 + 高 weight 提议 L1 promote |

## 路由决策表 (router, 按顺序匹配)

| 顺序 | 信号 | 目标 | 模式 |
| --- | --- | --- | --- |
| 1 | `frontmatter.type=domain` + `area` 字段 | `领域/<area>/<sub or "general">/` | auto |
| 2 | URL (frontmatter `source` 或正文 https?://) | `项目/<host>/<owner>/<repo>/` (github/gitlab/bitbucket) 或 `项目/<host>/...` | auto |
| 3 | 关键词 `永远 / 硬性 / never / 严禁 / 绝不` | `memory/L0-core/` | **ask** (env `CORTEX_EXTRACT_L0_AUTO`) |
| 4 | 关键词 `永久记住 / 长期保留` | `memory/L1-long/` | auto |
| 5 | 关键词 `记住 / 以后也用` | `memory/L2-mid/` | auto |
| 6 | 关键词 `暂时 / 临时 / 这次` 或 **无信号** (默认) | `memory/L3-short/` | auto |
| 7 | 复用 ≥ 3 (跨条目) | 在 L3 上附加 `promote-L2` 标 | 自动标记 |
| 8 | 复用 ≥ 5 + weight ≥ 0.8 | 在 L2/L3 上附加 `promote-L1` 标 | 自动标记 |

**L0 永远 ask**: 即使 `--apply`, L0 候选也通过 env `CORTEX_EXTRACT_L0_AUTO` (accept/reject/ask) mock 决策. 默认 `ask` 阻断 (非交互场景必须显式设值).

## 增量游标

`<target>/state/extract-cursor.json`:

```json
{
  "last_processed_mtime": 1717900000.0,
  "processed": ["<sha256>", ...]
}
```

- 每次 `--apply` 后写入
- `--no-cursor` 忽略游标 (强制全量)
- 下次扫: 仅处理 (mtime > last_processed_mtime) 且 (sha256 ∉ processed) 的条目

## dry-run 输出格式

```json
{
  "mode": "dry-run",
  "target": "/abs/path",
  "plan": [
    {
      "source": "/abs/.../L4-inbox/foo.md",
      "sha256": "abc...",
      "mtime": 1717900000.0,
      "weight": 0.5,
      "reuse_count": 1,
      "kw_hits": {"L3": ["暂时"]},
      "target": {
        "module": "memory",
        "level": "L3",
        "path": "memory/L3-short",
        "filename": "foo.md"
      },
      "reason": "L3 关键词命中: ['暂时']",
      "ask": false,
      "promote_hint": null
    }
  ],
  "skipped": [{"rel": "...", "sha256": "...", "reason": "cursor skip"}]
}
```

## apply 行为

1. 目标目录不存在则创建
2. 同名冲突: 追加 `.1 / .2 / ...` 后缀, **不覆盖**
3. 原 inbox 文件移到 `<target>/.wiki/memory/L4-inbox/_archived/`, **不 delete**
4. L0 候选: 走 `CORTEX_EXTRACT_L0_AUTO` env (accept/reject/ask). reject 时保留在 inbox, 不归档.
5. 游标更新: 写入 `last_processed_mtime` (max) + `processed` (sha256 list)

## 典型使用

```bash
# 1. 例行整理 (查看计划)
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target ~/.cortex \
  | python3 -m json.tool

# 2. 检查后落盘 (L0 候选自动拒绝以防误)
CORTEX_EXTRACT_L0_AUTO=reject bash plugins/tools/cortex/scripts/extract.sh \
  --apply --target ~/.cortex

# 3. 项目级 vault
bash plugins/tools/cortex/scripts/extract.sh --apply --target "$PWD/.wiki"
# 注: 项目级游标走 <repo>/.wiki/state/, 与用户级游标互不干扰

# 4. 重置游标全量重跑
bash plugins/tools/cortex/scripts/extract.sh --dry-run --no-cursor --target ~/.cortex
```

## 与其它 skill 的关系

- 路径目标定义: `cortex-schema-knowledge` (项目/领域/脚本 三模块) + `cortex-schema-memory` (L0-L4)
- 路径名与 level 一致性: `cortex-lint` R6 二次校验 (extract 写完跑 lint 验收)
- 单一真相: `docs/layout.md`

## 健壮性

- frontmatter 解析: 优先 pyyaml, 不可用时 fallback 简易 K:V parser (仅 scalar + flow list)
- 路由失败兜底: 保留 L4-inbox 加 `archive` 标 (不自动写 L0)
- sha256 + mtime 双键去重: 即使 mtime 回拨也不会重复处理
- 同名冲突: `.N` 后缀, 永不覆盖
- archive (不 delete): 用户可手动从 `_archived/` 恢复
