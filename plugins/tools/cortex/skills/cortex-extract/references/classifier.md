# classifier — 三轴 + 8 顺序路由决策

> 路径权威: `cortex-schema/references/knowledge-modules.md` (三模块) + `cortex-schema/references/memory-levels.md` (memory 5 级). 本文件只定义**算法**, 不重复路径段.

## 三轴信号源

| 轴 | 信号源 | 用途 |
| --- | --- | --- |
| 抗遗忘度 | 文件 mtime + frontmatter `created` | 老条目优先 promote; 新条目默认 L3 |
| 强度 | frontmatter `weight` (0-1); 关键词推断 (永远→1.0 / 暂时→0.3 / 默认 0.5) | 决定 L0/L1/L2/L3 候选 |
| 复用面 | inbox 内 token overlap (阈值 3 个相同 token 视为复用) | ≥ 3 提议 L2 promote, ≥ 5 + 高 weight 提议 L1 promote |

## 路由决策表 (router, 按顺序匹配)

| 顺序 | 信号 | 目标模块 (权威路径见 schema-*) | 模式 |
| --- | --- | --- | --- |
| 1 | `frontmatter.type=domain` + `area` 字段 | 领域模块 (见 cortex-schema/references/knowledge-modules.md) | auto |
| 2 | URL (frontmatter `source` 或正文 https?://) | 项目模块 (见 cortex-schema/references/knowledge-modules.md) | auto |
| 3 | 关键词 `永远 / 硬性 / never / 严禁 / 绝不` | memory L0 (见 cortex-schema/references/memory-levels.md) | **ask** (env `CORTEX_EXTRACT_L0_AUTO`) |
| 4 | 关键词 `永久记住 / 长期保留` | memory L1 (见 cortex-schema/references/memory-levels.md) | auto |
| 5 | 关键词 `记住 / 以后也用` | memory L2 (见 cortex-schema/references/memory-levels.md) | auto |
| 6 | 关键词 `暂时 / 临时 / 这次` 或 **无信号** (默认) | memory L3 (见 cortex-schema/references/memory-levels.md) | auto |
| 7 | 复用 ≥ 3 (跨条目) | 在 L3 上附加 `promote-L2` 标 | 自动标记 |
| 8 | 复用 ≥ 5 + weight ≥ 0.8 | 在 L2/L3 上附加 `promote-L1` 标 | 自动标记 |

## 反直觉提醒 (路径名防写反)

**默认入口 = L3 (短期, 最易遗忘)**, 不是 L1. 升级方向 = 抵抗遗忘: L3 → L2 → L1 → L0. 完整 level↔dir 映射 + 后缀规则权威见 `cortex-schema/references/memory-levels.md`.

## L0 永远 ask

即使 `--apply`, L0 候选也通过 env `CORTEX_EXTRACT_L0_AUTO` (accept/reject/ask) mock 决策. 默认 `ask` 阻断 (非交互场景必须显式设值).

## 健壮性

- frontmatter 解析: 优先 pyyaml, 不可用时 fallback 简易 K:V parser (仅 scalar + flow list)
- 路由失败兜底: 落 L4-inbox 加 `archive` 标 (不自动写 L0)
- sha256 + mtime 双键去重: 即使 mtime 回拨也不会重复处理
