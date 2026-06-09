---
name: cortex-extract
description: "extract/提取/promote/整理/归档/digest L4-inbox 收件箱, 按三轴 (抗遗忘度/强度/复用面) 路由到 L1-long/L2-mid/L3-short/项目/领域, 默认 dry-run JSON plan, --apply 落盘 + 增量游标. 用户说 '整理 inbox / 提取记忆 / 归档笔记 / promote / digest' 时使用."
when_to_use: "整理 inbox/提取 L4/归档临时笔记/extract/digest/promote 记忆/例行扫描 L4-inbox"
argument-hint: "[--dry-run|--apply] [target]"
arguments: "[--dry-run|--apply] [路径]"
---

# cortex-extract

L4-inbox → 项目/领域/memory 路由提取器. 默认 dry-run; `--apply` 才落盘. **默认入口 = L3-short** (短期, 最易遗忘), 升级方向 = 抗遗忘 (L3→L2→L1→L0).

## 路由速查表 (按顺序匹配, 先命中先用)

| # | 信号 | 目标 | 模式 |
| --- | --- | --- | --- |
| 1 | `type=domain` + `area` | `领域/<area>/<sub>/` | auto |
| 2 | URL (source / 正文) | `项目/<host>/<owner>/<repo>/` | auto |
| 3 | kw `永远/硬性/never/严禁/绝不` | `memory/L0-core/` | **ask** |
| 4 | kw `永久记住/长期保留` | `memory/L1-long/` | auto |
| 5 | kw `记住/以后也用` | `memory/L2-mid/` | auto |
| 6 | kw `暂时/临时/这次` 或无信号 | `memory/L3-short/` (默认) | auto |
| 7 | 复用 ≥ 3 | 附 `promote-L2` 标 | mark |
| 8 | 复用 ≥ 5 + weight ≥ 0.8 | 附 `promote-L1` 标 | mark |

路径名严格 `L0-core/L1-long/L2-mid/L3-short/L4-inbox`; 三模块目录中文 (项目/领域/脚本).

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查三轴信号源 + 8 顺序决策细节 | `references/classifier.md` |
| 查游标 + dry-run JSON 字段 + apply 行为 | `references/io.md` |
| 查 extract.sh 入口 + 调用示例 + L0 mock env | `references/usage.md` |
