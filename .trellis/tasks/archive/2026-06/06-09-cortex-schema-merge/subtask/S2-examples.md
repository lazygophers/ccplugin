---
id: S2
slug: examples
deliverable: D2
parent-task: 06-09-cortex-schema-merge
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S5]
estimated-tokens: 7000
---

# S2 · 写完整 .md 样例集

## 产出

`skills/cortex-schema/references/examples/` 含 7 文件:

| 文件 | type | level | 落盘位置 (示意) |
| --- | --- | --- | --- |
| rule.md | rule | L0 | memory/L0-core/never-commit-secrets.md |
| project.md | project | — | 项目/github.com/lazygophers/ccplugin/README.md |
| domain.md | domain | — | 领域/tech/rust/async/tokio-runtime.md |
| memory-L1.md | memory | L1 | memory/L1-long/shell-quoting-rules.md |
| memory-L2.md | memory | L2 | memory/L2-mid/current-sprint-context.md |
| memory-L3.md | memory | L3 | memory/L3-short/today-tmp-fix.md |
| vault-script.md | vault-script | — | 脚本/canvas-from-mindmap.py (本文为描述, 非可执行) |

## 内容契约 (每个样例)

1. 头部 1 行注释: `> 样例 — type=X, 完整可直接落盘到 <path>`
2. 完整 frontmatter (含 type/level (如适用)/created/updated/tags/aliases/weight)
3. 正文 ≥ 5 行 (有意义, 非 lorem ipsum)
4. 至少 1 个 wikilink (`[[other-page]]`) 演示
5. 至少 1 个 `## ` 二级标题
6. 文件 ≤ 80 行

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema/references/examples
test -d $d
count=$(/usr/bin/find $d -name '*.md' -type f | wc -l | tr -d ' ')
[[ $count -ge 5 ]] || { echo "FAIL: examples < 5 (got $count)"; exit 1; }
for f in rule project domain memory-L1 memory-L2 memory-L3 vault-script; do
  test -f $d/$f.md || echo "MISSING: $f.md"
done
# 每个样例含 frontmatter + 标题 + wikilink
for f in $d/*.md; do
  grep -q '^---$' $f || echo "FAIL: $f no frontmatter"
  grep -q '^## ' $f || echo "FAIL: $f no h2"
  grep -q '\[\[' $f || echo "FAIL: $f no wikilink"
done
```

## 资源

独占 `skills/cortex-schema/references/examples/**` (新建).

## 执行细节

1. 不依赖其他 subtask, 直接按下方模板写 7 文件
2. 每文件可独立交付, 不互相依赖
3. wikilink 互相引用 OK (跨样例 wikilink, 体现 vault 互联)

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-merge

## 目标
建 7 完整 .md 样例文件到 plugins/tools/cortex/skills/cortex-schema/references/examples/. 每个含完整 frontmatter + 正文 ≥ 5 行 + ≥ 1 wikilink + ≥ 1 ## 标题 + 顶部 1 行注释指明落盘位置.

## 7 文件清单
- rule.md (type=rule, level=L0; 例: 永远不提交凭证)
- project.md (type=project; 例: ccplugin 仓库摘要)
- domain.md (type=domain, area=tech; 例: tokio runtime 笔记)
- memory-L1.md (type=memory, level=L1; 例: shell quoting 规则)
- memory-L2.md (type=memory, level=L2; 例: 当前 sprint 上下文)
- memory-L3.md (type=memory, level=L3; 例: 今天的临时 fix)
- vault-script.md (type=vault-script; 描述一个 canvas-from-mindmap.py 脚本; 用 markdown 描述脚本而非 .sh 文件)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-schema/references/examples/** (新建)
禁改: 其他任何文件

## 样例内容质量要求
- frontmatter 字段齐 (created/updated 用 2026-06-09; tags 列出真实词; aliases 列 1-2 个)
- 正文是真实有意义的小笔记 (而非 "TODO: fill")
- wikilink 跨样例引用 (e.g. memory-L3 引 [[today-tmp-fix]] 或引另一个样例 alias)
- 每文件 ≤ 80 行

## 验收
subtask "验证" 节命令全过, 无 FAIL/MISSING.

## 失败处理
- 工具错 → 重试 1 次
- 不确定字段语义 → 引 schema-knowledge/templates.md (源)

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
rm -rf plugins/tools/cortex/skills/cortex-schema/references/examples/
```
