---
id: S4
slug: extract-dedup
deliverable: D4
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: sub-agent
depends-on: [S1, S2]
blocks: [S6]
estimated-tokens: 6000
---

# S4 · extract references 去重

## 目标

extract references 删除路径段硬列 (项目/<host>/<owner>/<repo>/ 等), 仅留三轴 + 8 顺序决策 + 行为, 路径权威全部引用 schema-*.

## 产出

- 改 `references/classifier.md`:
  - 8 顺序决策表中目标列改"见 cortex-schema-knowledge/references/projects.md" 等
  - 三轴定义不变 (算法)
  - 路径名后缀防写反提醒可保留一行 (与 schema-memory R6 一致), 但不重复完整映射
- 改 `references/io.md`: dry-run JSON 字段保留, 路径示例改 "<schema 决定的路径>"
- `references/usage.md`: 不变 (是 CLI 用法, 不含路径定义)

SKILL.md 路由速查表保留 (薄入口允许 1 行/路径)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-extract
# 路径硬列删干净
hits=$(grep -E '项目/<host>|领域/<area>|memory/L[0-9]-(core|long|mid|short|inbox)' $d/references/classifier.md | grep -v '\[.*\](' | wc -l | tr -d ' ')
[[ $hits -le 2 ]] || echo "FAIL: classifier.md still hardlists $hits paths"
# 必备引用
grep -q 'cortex-schema-knowledge\|schema-knowledge' $d/references/classifier.md
grep -q 'cortex-schema-memory\|schema-memory' $d/references/classifier.md
# 三轴 + 8 顺序保留
grep -q '三轴\|抗遗忘度' $d/references/classifier.md
grep -q '顺序\|sequence' $d/references/classifier.md
```

## 资源

独占 `skills/cortex-extract/references/**`.

## 执行细节

1. Read 既有 `references/classifier.md`
2. 改 8 顺序决策表:
   ```
   | # | 信号 | 目标模块 (权威路径见 schema-*) | 模式 |
   | 1 | type=domain + area | 领域 (cortex-schema-knowledge/references/domains.md) | auto |
   | 2 | URL | 项目 (cortex-schema-knowledge/references/projects.md) | auto |
   | 3 | "永远/硬性" kw | L0-core (cortex-schema-memory/references/levels.md#L0) | ask |
   ...
   ```
   保留信号列 + 模式列, 目标列改成引用语句.
3. 三轴定义段不动
4. 路径名后缀防写反一句话保留 (引 schema-memory)
5. Read `references/io.md`: dry-run JSON plan 字段中 `target.path` 字段说明改为"取值由 schema-* 决定", 但 JSON 结构不变 (是数据契约)
6. usage.md 不动

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-sot

## 目标
cortex-extract references 去除路径硬列, 引用 cortex-schema-knowledge / cortex-schema-memory 替代.

## 已知
- schema-* 已含完整路径权威 (S1/S2 已完成)
- 8 顺序路由表算法不变, 仅目标路径列改引用
- 三轴算法不变
- dry-run JSON 字段保留 (数据契约)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-extract/references/**
禁改: SKILL.md (路由速查保留) / scripts/_extract/ (代码不动)

## 验收
subtask "验证" 节命令全过.

## 失败处理
- 工具错 → 重试 1 次
- 数据契约部分 (JSON plan) 必须保留, 仅删可引用替代的路径列表

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-extract/references/
```
