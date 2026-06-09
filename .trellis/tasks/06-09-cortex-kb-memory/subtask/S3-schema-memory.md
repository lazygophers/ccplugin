---
id: S3
slug: schema-memory
deliverable: D3
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: sub-agent
isolation: none
depends-on: [S1]
blocks: [S4, S5, S6]
estimated-tokens: 10000
---

# S3 · 写 cortex-schema-memory skill

## 目标

落一份记忆等级契约 skill, 把 L0 核心 / L1 长期 / L2 中期 / L3 短期 / L4 收件箱 五级的语义、目录、frontmatter、promote/demote/forget 规则写成可触发的 skill 文档。**等级按遗忘曲线设计**, 数字与"短/长期"非直觉对应, 必须在文档显式标注。

## 产出

- `plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md`
- frontmatter 含: `name: cortex-schema-memory`, `description` (前置触发词: "记忆 / memory / L0 / 永远 / 暂时 / 记住 / 忘了 / 遗忘"), `when_to_use`
- 主体五段: L0 核心 / L1 长期 / L2 中期 / L3 短期 / L4 收件箱, 各含定义 + 路径 + 写入触发 + 自动迁移规则
- 头部"等级速查"区: 一图说明遗忘曲线映射 (L3 易忘 → L1 稳固)
- 末段: 三轴定义 (抗遗忘度 / 强度 / 复用面) + extract 路由判定表

## 验证

```bash
test -f plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md
python3 -c "
import yaml
c = open('plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md').read()
fm = yaml.safe_load(c.split('---')[1])
assert fm['name'] == 'cortex-schema-memory'
assert any(k in fm['description'] for k in ['记忆','memory','L0','L4'])
print('OK')
"
for level in L0-core L1-long L2-mid L3-short L4-inbox; do
  grep -q "$level" plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md || echo "MISSING: $level"
done
grep -q '遗忘\|抗遗忘\|forgetting' plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md
grep -q 'promote\|晋级\|迁移' plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md
# 防"L1 短期"反写: L1 必须与"长期"出现在同段
grep -B0 -A2 'L1' plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md | grep -q '长期\|long' || echo "WARN: L1 语义未标长期"
```

期望: 全部退出 0; 输出 "OK"; 无 "MISSING"。

## 资源

- 独占文件: `plugins/tools/cortex/skills/cortex-schema-memory/**`
- 与 S2 不互斥
- 审批槽位: 否

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S1 | `docs/layout.md` 存在 | 文件检测 |

## 执行细节

按 design.md "契约: 记忆五级语义 (按遗忘曲线设计)" 表展开。**升级方向 (抵抗遗忘) = L3 → L2 → L1 → L0**, 不是 L0 → L4。

1. **L0 — 核心记忆** (`memory/L0-core/`)
   - 不进入遗忘曲线, 永久常驻, 不可违反
   - 写入触发: 用户显式 "永远 / 硬性 / never / 严禁"
   - frontmatter: `type: rule` `level: L0` `weight: 1.0` `created` `aliases`
   - forget 仅手动, 永不自动降级
2. **L1 — 长期记忆** (`memory/L1-long/`)
   - 遗忘曲线尾端: 已稳固, 几乎不忘; 高强度, 跨项目稳定
   - 写入: L2 访问 ≥ 5 次 + 评分 ≥ 0.8 promote, 或用户 "永久记住"
   - 365 天未访问 → demote 到 L2 (不自动 forget, lint 标记)
3. **L2 — 中期记忆** (`memory/L2-mid/`)
   - 遗忘曲线中段: 周月级巩固; 较高强度, 跨任务同领域
   - 写入: L3 访问 ≥ 3 次 promote, 或用户 "记住"
   - 90 天未访问 → demote 到 L3
4. **L3 — 短期记忆** (`memory/L3-short/`)
   - 遗忘曲线头端: 最易遗忘; 中等强度, 当前任务/会话面
   - 写入: extract 默认入口 + 用户 "暂时 / 临时"
   - 7 天未访问 → forget 候选 (lint 标记, 不自动删)
5. **L4 — 收件箱** (`memory/L4-inbox/`)
   - 未进入曲线; 原始资料未分类
   - 写入: 任意来源直落
   - extract 处理后 archive (落到 L1/L2/L3) 或 delete (低价值)

末段:
- 三轴定义: 抗遗忘度 (天, L1=365 / L2=90 / L3=7) / 强度 (用户标注 0-1) / 复用面 (会话数)
- extract 路由判定表: 默认入口 L3; 复用 ≥ 3 → L2 候选; 复用 ≥ 5 + weight ≥ 0.8 → L1 候选; "永远/硬性" 关键词 → L0 (ask)
- 在头部加一张 "等级速查" 表格或 ASCII 图: `L3 短期 (易忘) ─ promote → L2 ─ promote → L1 长期 (稳固) ─ promote → L0 核心`

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-kb-memory

## 目标
写 cortex-schema-memory skill (产出节文件), 严格按 design.md "契约: 记忆五级语义" 表 + 本 subtask "执行细节" 五段展开, 末段加三轴 + 路由表。

## 已知
- 上游: docs/layout.md (S1)
- 5 级 (按遗忘曲线): L0 核心 / L1 长期 / L2 中期 / L3 短期 / L4 收件箱
- 路径: memory/L0-core memory/L1-long memory/L2-mid memory/L3-short memory/L4-inbox
- promote 方向: L3 → L2 → L1 → L0 (抗遗忘); demote 反向

## 工作目录与范围
- cwd: /Users/luoxin/persons/lyxamour/ccplugin
- 可改: plugins/tools/cortex/skills/cortex-schema-memory/**
- 禁改: 其他 plugins/tools/cortex/; .trellis/**

## 输出格式
- SKILL.md ≤ 220 行

## 验收标准
subtask "验证" 节全部命令通过, 输出 "OK", 无 "MISSING"。

## 失败处理
- 工具错 → 重试 1 次
- 不确定 → "需要: <问题>" 回 main
- 资源不可用 → Blocked

## Sub-agent 自防护
trellis-implement, 不再 spawn。
```

## 回滚

- 触发条件: frontmatter 不合法 或 五级语义有矛盾
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/skills/cortex-schema-memory/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| L1/L2/L3 分界不明确 | extract 路由错配 | 用三轴+硬阈值 (L3=7d / L2=90d / L1=365d + 访问次数) 而非主观判断 |
| 反直觉等级语义 (L1 是长期不是短期) 导致下游路径名写反 | extract/lint 写到错误目录 | 路径名内嵌语义 (L1-long / L3-short); skill 头部"等级速查"区一图说明; lint R6 检测路径名与级别一致 |
| 抗遗忘度阈值不合用户实际 | 长期未访问数据被错降级 | G1 让用户确认阈值, 阈值写在 skill 而非脚本里 |
| L0 被自动写入风险 | 行为规范污染 | L0 写入路径只接受显式关键词 (永远/硬性/never), extract 不会路由到 L0 |

## 历史

- 2026-06-09: created
