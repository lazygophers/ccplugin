---
id: S1
slug: skill-build
deliverable: D1,D3
parent-task: 06-09-cortex-schema-merge
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S3, S4, S5]
estimated-tokens: 12000
---

# S1 · 建 cortex-schema 新 skill

## 产出

- `skills/cortex-schema/SKILL.md` (≤ 60 行)
- `skills/cortex-schema/references/topology.md` (顶层 + .wiki 物理树 + 详细 ASCII 含示例叶子)
- `skills/cortex-schema/references/knowledge-modules.md` (项目/领域/脚本 三模块路径规则)
- `skills/cortex-schema/references/memory-levels.md` (5 级 + 映射 + 反写防呆 + 遗忘曲线)
- `skills/cortex-schema/references/templates.md` (frontmatter 字段 + 各 type 块模板)

## 源 (必读)

- `skills/cortex-schema-knowledge/SKILL.md` + references/topology.md + templates.md + projects.md + domains.md + scripts.md
- `skills/cortex-schema-memory/SKILL.md` + references/levels.md + axes-routing.md + properties.md

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema
test -f $d/SKILL.md
test -f $d/references/topology.md
test -f $d/references/knowledge-modules.md
test -f $d/references/memory-levels.md
test -f $d/references/templates.md
[[ $(wc -l < $d/SKILL.md) -le 60 ]] || { echo "FAIL SKILL.md too long"; exit 1; }
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-schema'
desc, wtu, args = fm['description'], fm['when_to_use'], fm['arguments']
assert len(desc) <= 512 and len(wtu) <= 128
assert '用户说' not in desc and '用户说' not in wtu
assert isinstance(args, str)
print('OK')
"
# 详细 ASCII 含示例叶子
grep -q 'README.md\|design.md\|tokio\|never-commit\|sleep-protocol' $d/references/topology.md
# 5 级与三模块齐
for t in 'L0-core' 'L1-long' 'L2-mid' 'L3-short' 'L4-inbox' '项目' '领域' '脚本'; do
  grep -ql "$t" $d/references/*.md || echo "MISSING: $t"
done
```

## 资源

独占 `skills/cortex-schema/**` (新建). 读 `skills/cortex-schema-{knowledge,memory}/**` (源).

## 执行细节

1. Read 全部 schema-knowledge / schema-memory references
2. 合并:
   - topology.md = schema-knowledge/topology.md 内容 + 详细 ASCII (含示例叶子, 如 design.md 中 ASCII)
   - knowledge-modules.md = schema-knowledge/{projects, domains, scripts}.md 三个合一; 路径/frontmatter/命名 三段
   - memory-levels.md = schema-memory/{levels, axes-routing, properties}.md 三个合一
   - templates.md = schema-knowledge/templates.md (frontmatter 通用字段表 + 各 type 块模板)
3. SKILL.md 薄入口:
   - frontmatter (含 arguments 字符串)
   - 1 段总览 (统一契约 + 单一真相)
   - 三模块速查表 (3 行) + 5 级速查表 (5 行)
   - 路由表 (5 项 → references)
   - 引用 lint/extract

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-merge

## 目标
建 cortex-schema 新 skill, 合并 cortex-schema-knowledge + cortex-schema-memory 的 references 内容. SKILL.md ≤ 60 行薄入口 + 4 references (topology/knowledge-modules/memory-levels/templates).

## 已知 (源, 必读)
- plugins/tools/cortex/skills/cortex-schema-knowledge/{SKILL.md, references/{topology,templates,projects,domains,scripts}.md}
- plugins/tools/cortex/skills/cortex-schema-memory/{SKILL.md, references/{levels,axes-routing,properties}.md}

## 路径与约定 (不变)
- 三模块中文: 项目/领域/脚本
- 5 级英文: memory/L0-core L1-long L2-mid L3-short L4-inbox
- 升级方向: L3→L2→L1→L0; 默认入口 L3
- 双层同构: ~/.cortex/.wiki + <repo>/.wiki
- 反直觉: L1=长期 L3=短期

## frontmatter
```yaml
---
name: cortex-schema
description: "项目知识库统一契约 — 目录结构 / 三模块路径 (项目/领域/脚本) / 5 级记忆 (L0-core/L1-long/L2-mid/L3-short/L4-inbox, Ebbinghaus 遗忘曲线) / 双层同构 (~/.cortex/.wiki + <repo>/.wiki) / frontmatter 模板 / 完整样例. lint+extract 引用本 skill 作权威源."
when_to_use: "入库/归档/写笔记/记忆等级判定/promote/demote/forget/路径决策/frontmatter 模板/查样例"
argument-hint: "[topology|knowledge|memory|templates|examples]"
arguments: "[拓扑|知识|记忆|模板|样例]"
---
```

## SKILL.md 结构 (≤ 60 行)
1. frontmatter
2. 1 段总览
3. 三模块速查表 (3 行 + 用途分离一句话)
4. 5 级速查 ASCII 图 (反直觉提醒)
5. 路由表 (5 项指向 references)
6. 引用 lint/extract

## references 内容

### topology.md (≤ 220 行)
- ~/.cortex/ 顶层布局
- <repo>/.wiki/ 物理树
- 双层同构原则
- 开放扩展位
- 脚本目录用途分离表 (顶层 scripts/ vs .wiki/脚本/)
- 必备目录清单
- **详细 ASCII (新)** 含示例文件叶子:
  ```
  ~/.cortex/.wiki/
  ├── memory/L0-core/never-commit-secrets.md
  ├── memory/L1-long/shell-quoting-rules.md
  ├── memory/L2-mid/current-sprint-context.md
  ├── memory/L3-short/today-tmp-fix.md
  ├── memory/L4-inbox/pasted-note.md
  ├── 项目/github.com/lazygophers/ccplugin/{README.md, mindmap.canvas, notes/architecture.md}
  ├── 领域/tech/rust/async/tokio-runtime.md
  ├── 领域/life/habits/sleep-protocol.md
  ├── 领域/finance/etf/global-allocation.md
  └── 脚本/{canvas-from-mindmap.py, frontmatter-normalize.sh}
  ```

### knowledge-modules.md (≤ 220 行)
三段合一 (项目/领域/脚本), 每段含路径规则 + 命名约定 + frontmatter 关键字段 + (引用 examples/<type>.md 看完整样例)

### memory-levels.md (≤ 220 行)
- 等级速查 ASCII (反直觉)
- L0-L4 五段
- level↔dir 映射表
- 反写防呆清单
- 三轴定义 + extract 路由判定表
- 关键性质 (默认 L3 / promote 离线 / forget 不自动)

### templates.md (≤ 220 行)
- frontmatter 通用字段表
- 各 type frontmatter 块模板 (project/domain/rule/memory/vault-script)
- (引用 examples/<type>.md 看完整文件样例)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-schema/** (新建)
禁改: 旧 schema-{knowledge,memory}/ (S3 删, 你不要动); lint/extract; agent; 脚本

## 验收
subtask "验证" 节命令全过, 输出 OK, 无 MISSING.

## 失败处理
- 工具错 → 重试 1 次
- references 超 220 行 → 砍冗余, 不丢核心
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
rm -rf plugins/tools/cortex/skills/cortex-schema/
```
