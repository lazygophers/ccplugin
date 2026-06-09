---
id: S2
slug: schema-memory
deliverable: D2,D5
parent-task: 06-09-cortex-skills-multifile
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S5]
estimated-tokens: 8000
---

# S2 · 拆 cortex-schema-memory 为多文件

## 目标

拆成 SKILL.md (≤ 60 行) + references/{levels,axes-routing,properties}.md, 同改 frontmatter (description ≤ 512 / when_to_use ≤ 128 / 新增 arguments).

## 产出

- `skills/cortex-schema-memory/SKILL.md` (覆盖)
- `references/levels.md` (L0-L4 五段)
- `references/axes-routing.md` (三轴 + extract 路由表)
- `references/properties.md` (关键性质 + 速查图)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema-memory
test -f $d/SKILL.md && test -d $d/references
[[ $(/usr/bin/find $d/references -name '*.md' | wc -l | tr -d ' ') -ge 3 ]]
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-schema-memory'
assert len(fm['description']) <= 512
wtu = fm['when_to_use'] if isinstance(fm['when_to_use'], str) else '/'.join(fm['when_to_use'])
assert len(wtu) <= 128
assert fm.get('arguments') and len(fm['arguments']) >= 1
print('OK')
"
```

## 资源

独占 `skills/cortex-schema-memory/**`, 与他人不互斥.

## 执行细节

SKILL.md 必含: 反直觉等级速查 ASCII 图 (L3 短期 → L2 → L1 长期 → L0) + 路由表.

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-skills-multifile

## 目标
拆 plugins/tools/cortex/skills/cortex-schema-memory/SKILL.md 单文件 → SKILL.md (≤ 60 行) + references/{levels.md, axes-routing.md, properties.md}. 改 frontmatter description ≤ 512 / when_to_use ≤ 128 / 加 arguments.

## 已知 (反直觉)
等级按 Ebbinghaus 遗忘曲线: L0 核心 / L1 长期 / L2 中期 / L3 短期 / L4 收件箱. 升级方向 = 抗遗忘 (L3→L2→L1→L0). 默认入口 L3-short. 路径名后缀强制内嵌语义.

## frontmatter arguments
arguments:
  - name: level
    description: "L0 | L1 | L2 | L3 | L4, 限定查特定级别, 不填则全部"
    required: false
    type: enum
    values: [L0, L1, L2, L3, L4]
argument-hint: "[level]"

## SKILL.md 内容
1. frontmatter
2. 1 段总览 + 反直觉警告
3. 速查 ASCII 图:
   L3 短期 (易忘) ─ promote → L2 中期 ─ promote → L1 长期 (稳固) ─ promote → L0 核心
        7d 阈值              90d 阈值              365d 阈值              永久, 仅手动
4. 路由表:
   | 任务 | 文件 |
   | 查 L0-L4 各级语义 / 路径 / 迁移 | references/levels.md |
   | 查三轴 + extract 路由判定表 | references/axes-routing.md |
   | 查关键性质 (默认入口/促进/forget) | references/properties.md |

## references 内容
- levels.md: L0/L1/L2/L3/L4 五段, 每段 (定义 + 路径 + 写入触发 + 自动迁移 + frontmatter)
- axes-routing.md: 三轴定义 + extract 路由判定表 (default L3, ≥3 → L2, ≥5+w≥0.8 → L1, "永远" → L0 ask)
- properties.md: 默认入口 L3 / promote 离线触发 / forget 不自动 / 反直觉 L1=长期 提醒 / lint R6 护栏

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-schema-memory/**

## 验收
subtask "验证" 节全过.

## 失败处理
- 工具错 → 重试 1 次
- 字符上限超 → 砍内容到 references, 不丢触发词 (记忆/memory/L0-L4/永远/暂时/记住/忘了/遗忘)

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-schema-memory/
```
