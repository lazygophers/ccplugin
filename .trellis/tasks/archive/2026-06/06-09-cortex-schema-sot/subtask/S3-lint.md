---
id: S3
slug: lint-dedup
deliverable: D3
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: sub-agent
depends-on: [S1, S2]
blocks: [S6]
estimated-tokens: 7000
---

# S3 · lint references 去重

## 目标

lint references 删除路径段硬列, 仅留 R1-R7 算法描述, 路径权威全部引用 cortex-schema-knowledge / cortex-schema-memory.

## 产出

- 改 `references/rules.md`:
  - R3 命名: 删 `领域/<area>/<sub>/` 硬列, 改"命名约定见 cortex-schema-knowledge/references/{domains,scripts}.md"
  - R4 同构: 删必备目录硬列, 改"必备目录清单见 cortex-schema-knowledge/references/topology.md + cortex-schema-memory/references/levels.md"
  - R6 等级语义: 删 level↔dir 映射表, 改"权威映射见 cortex-schema-memory/references/levels.md"
  - R1/R2/R5/R7 算法描述基本保留 (这些不依赖具体路径)
- 改 `references/fixers.md`: R2 推断表中 type→路径前缀 改为"按 cortex-schema-knowledge 模块判定" (保留算法, 删硬列)

SKILL.md 7 规则速查表不变.

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-lint
# 路径硬列删干净 (允许在测试命令示例 / 代码段中出现, 排除 ```code 段)
# 简单实现: grep 整文件, 命中 <= 3 (容忍 markdown link 中含路径段)
hits=$(grep -E 'memory/L[0-9]-(core|long|mid|short|inbox)' $d/references/rules.md | grep -v '\[.*\](' | wc -l | tr -d ' ')
[[ $hits -le 2 ]] || echo "FAIL: rules.md still hardlists $hits paths"
# 必备引用存在
grep -q 'cortex-schema-knowledge\|schema-knowledge' $d/references/rules.md
grep -q 'cortex-schema-memory\|schema-memory' $d/references/rules.md
# 算法描述保留 (R1-R7 全部仍有定义段)
for r in R1 R2 R3 R4 R5 R6 R7; do
  grep -q "^##.*$r\| $r " $d/references/rules.md || echo "MISSING: $r"
done
```

## 资源

独占 `skills/cortex-lint/references/**`.

## 执行细节

1. Read 既有 `references/rules.md`
2. 改:
   - R3: 删命名规则细节硬列 (`domains/ < 2 级` 路径示例), 留检测策略 (`检测: 路径段数 < 4 → 报警, 详细规则见 schema-knowledge`)
   - R4: 删 `VAULT_REQUIRED_DIRS` 硬列, 改"必备目录清单由 cortex-schema-knowledge (顶层 + 三模块) + cortex-schema-memory (5 级) 共同定义. 缺失则 R4 报 error + autofix mkdir."
   - R6: 删完整映射表, 留"R6 检测路径名 ↔ frontmatter level 字段一致; 权威映射见 cortex-schema-memory/references/levels.md. 反写 (L1-recent/L1-short/L3-long 等) 视 error."
3. Read `references/fixers.md`:
   - R2 推断表 type 列: 删硬列, 改 "按 cortex-schema-knowledge 三模块路径前缀判定"
   - R4 mkdir 列表删, 改引用
4. SKILL.md 不动

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-sot

## 目标
cortex-lint references 去除路径/结构硬列重复, 改为引用 cortex-schema-knowledge / cortex-schema-memory.

## 已知
- schema-knowledge 已含: 顶层布局 + 三模块路径 + 必备目录 + 用途分离 + frontmatter 模板 (references/topology.md / templates.md / projects.md / domains.md / scripts.md)
- schema-memory 已含: 5 级物理树 + level↔dir 映射表 + 遗忘曲线 + 反写防呆 (references/levels.md)
- 7 规则不变, 仅删路径硬列

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-lint/references/**
禁改: SKILL.md (7 规则速查表不动) / scripts/_lint/ (代码不动)

## 输出
- rules.md / fixers.md 保留 R1-R7 算法, 删路径硬列, 加 schema-* 引用

## 验收
subtask "验证" 节命令全过 (路径硬列命中 ≤ 2, schema-* 引用 ≥ 1)

## 失败处理
- 工具错 → 重试 1 次
- 算法部分必须保留, 仅删可被引用替代的路径列表

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-lint/references/
```
