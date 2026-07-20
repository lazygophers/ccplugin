# core-downgrade — 详细设计

## 用户确认 (2026-07-20)
- core spec 8500 > 8000 上限, 降 3 条最彻底

## 降级方案
移 3 文件 layer core→recall + 物理目录迁移 + frontmatter 改 + reindex:
1. `core/impl/sediment-51.md` → `recall/impl/sediment-51.md` (正向表述优先原则, 617 字符)
2. `core/consistency/rule-53.md` → `recall/consistency/rule-53.md` (对外插件清单单真源, 590 字符)
3. `core/test/sediment-52.md` → `recall/test/sediment-52.md` (独立验证防自评偏差, 585 字符)

frontmatter 每条改 `layer: core` → `layer: recall`。recall/consistency 类目需新建(若不存在)。

## 验证
- `skein-spec maintain` 无超预算告警
- `skein-spec inject-core | wc -c` 显著下降(目标 < 8000, 预期约 6700)
- `skein-spec reindex` 后 core/index.md + recall/index.md 均更新
- 3 条规则在 recall 可被关键词召回(quick recall 测)

## 执行
skein start → 派 skein-executor 在 worktree 内移动 + reindex → check(maintain + inject-core 验证)
