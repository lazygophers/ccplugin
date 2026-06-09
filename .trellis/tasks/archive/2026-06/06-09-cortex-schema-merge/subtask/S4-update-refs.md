---
id: S4
slug: update-refs
deliverable: D5
parent-task: 06-09-cortex-schema-merge
status: planned
execution-layer: sub-agent
depends-on: [S1]
blocks: [S5]
estimated-tokens: 8000
---

# S4 · 改全库引用指向 cortex-schema

## 产出

8 文件改引用 `cortex-schema-knowledge` / `cortex-schema-memory` → `cortex-schema`:

- `skills/cortex-lint/SKILL.md`
- `skills/cortex-lint/references/rules.md`
- `skills/cortex-lint/references/fixers.md`
- `skills/cortex-extract/references/classifier.md`
- `skills/cortex-extract/references/io.md`
- `agents/cortex.md`
- `README.md`
- `llms.txt`
- `scripts/_lint/__init__.py` (注释)
- `tests/e2e-report.md`

引用 references 子文件时:
- `cortex-schema-knowledge/references/topology.md` → `cortex-schema/references/topology.md`
- `cortex-schema-knowledge/references/templates.md` → `cortex-schema/references/templates.md`
- `cortex-schema-knowledge/references/{projects,domains,scripts}.md` → `cortex-schema/references/knowledge-modules.md`
- `cortex-schema-memory/references/levels.md` (含 properties / axes-routing) → `cortex-schema/references/memory-levels.md`

## 验证

```bash
! grep -rln 'cortex-schema-knowledge\|cortex-schema-memory' plugins/tools/cortex/ 2>&1 && echo "0 hits"
grep -rl 'cortex-schema' plugins/tools/cortex/ | grep -v '/cortex-schema/' | head -5
```

## 资源

写: 上面 10 文件. 与 S3 不互斥 (改不同文件).

## 依赖

S1 完成 (cortex-schema/references/* 已存在, 引用立得住)

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-merge

## 目标
把 plugins/tools/cortex/ 内所有 `cortex-schema-knowledge` / `cortex-schema-memory` 引用替换为 `cortex-schema`. references 子文件按映射:
- cortex-schema-knowledge/references/topology.md → cortex-schema/references/topology.md
- cortex-schema-knowledge/references/templates.md → cortex-schema/references/templates.md
- cortex-schema-knowledge/references/{projects,domains,scripts}.md → cortex-schema/references/knowledge-modules.md
- cortex-schema-memory/references/{levels,axes-routing,properties}.md → cortex-schema/references/memory-levels.md

## 已知改文件清单 (10)
- skills/cortex-lint/SKILL.md
- skills/cortex-lint/references/rules.md
- skills/cortex-lint/references/fixers.md
- skills/cortex-extract/references/classifier.md
- skills/cortex-extract/references/io.md
- agents/cortex.md
- README.md
- llms.txt
- scripts/_lint/__init__.py (注释)
- tests/e2e-report.md

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: 上述 10 个文件
禁改: skills/cortex-schema/** (S1 产出, 不动); skills/cortex-schema-{knowledge,memory}/** (S3 删, 不动); 其他

## 操作
先 grep 出每个文件中所有命中行, 用 Edit 工具按映射逐处替换. 不破坏内容结构, 仅换 skill 名 + reference 文件名.

## 验收
- `grep -rln 'cortex-schema-knowledge\|cortex-schema-memory' plugins/tools/cortex/` 0 命中
- 每个改过文件内仍含 `cortex-schema` 引用 (单数, 新名)

## 失败处理
- 工具错 → 重试 1 次
- 某文件引用语义不明 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/{skills/cortex-lint,skills/cortex-extract,agents,README.md,llms.txt,scripts/_lint/__init__.py,tests/e2e-report.md}
```
