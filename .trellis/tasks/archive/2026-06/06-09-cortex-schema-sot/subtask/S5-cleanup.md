---
id: S5
slug: cleanup-layout-refs
deliverable: D5,D6
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: main
depends-on: [S1, S2]
blocks: [S6]
estimated-tokens: 4000
---

# S5 · 删 docs/layout.md + 改全库引用

## 产出

- 删 `plugins/tools/cortex/docs/layout.md` (若 docs/ 空也删目录)
- 改 `plugins/tools/cortex/agents/cortex.md`: "目录契约权威" 引用从 layout.md 改 schema-*
- 改 `plugins/tools/cortex/README.md`: layout.md 链接改 schema-* skill 名
- 改 `plugins/tools/cortex/llms.txt`: 同上
- 改 `plugins/tools/cortex/scripts/validate-layout.sh` 注释: 引用 schema-* 而非 layout.md

## 验证

```bash
test ! -f plugins/tools/cortex/docs/layout.md
! grep -rl 'docs/layout.md' plugins/tools/cortex/ && echo "0 hits"
grep -q 'cortex-schema' plugins/tools/cortex/agents/cortex.md
grep -q 'cortex-schema' plugins/tools/cortex/README.md
grep -q 'cortex-schema' plugins/tools/cortex/llms.txt
grep -q 'cortex-schema' plugins/tools/cortex/scripts/validate-layout.sh
```

## 资源

- 写: agents/cortex.md / README.md / llms.txt / scripts/validate-layout.sh
- 删: docs/layout.md
- 主会话执行 (不派 sub-agent, 涉及多文件小改动 + 删文件)

## 依赖

S1+S2 完成 (schema-* 已含全部权威内容, 引用可立)

## 执行细节

1. rm docs/layout.md (+ rmdir docs/ 如空)
2. agents/cortex.md "引用 docs/layout.md" → "目录契约权威: cortex-schema-knowledge (顶层 + 三模块) + cortex-schema-memory (5 级)"
3. README.md "docs/layout.md" 链接 → skill 名引用
4. llms.txt 同
5. validate-layout.sh 注释中 "见 docs/layout.md" → "见 cortex-schema-knowledge/references/topology.md"

## 回滚

```bash
git checkout HEAD~ -- plugins/tools/cortex/docs/layout.md
git checkout plugins/tools/cortex/agents/cortex.md plugins/tools/cortex/README.md plugins/tools/cortex/llms.txt plugins/tools/cortex/scripts/validate-layout.sh
```
