---
id: S4
slug: extract
deliverable: D4,D5
parent-task: 06-09-cortex-skills-multifile
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S5]
estimated-tokens: 8000
---

# S4 · 拆 cortex-extract 为多文件

## 产出

- `skills/cortex-extract/SKILL.md` (覆盖, ≤ 60 行)
- `references/classifier.md` (三轴 + 8 顺序决策表)
- `references/io.md` (游标 + dry-run JSON + apply 行为)
- `references/usage.md` (extract.sh 入口 + 调用示例 + L0 mock env)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-extract
test -f $d/SKILL.md && [[ $(/usr/bin/find $d/references -name '*.md' | wc -l | tr -d ' ') -ge 3 ]]
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-extract'
assert len(fm['description']) <= 512
wtu = fm['when_to_use'] if isinstance(fm['when_to_use'], str) else '/'.join(fm['when_to_use'])
assert len(wtu) <= 128
assert fm.get('arguments') and len(fm['arguments']) >= 2
print('OK')
"
```

## 资源

独占 `skills/cortex-extract/**`.

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-skills-multifile

## 目标
拆 cortex-extract SKILL.md 单文件 → SKILL.md (≤ 60 行) + references/{classifier,io,usage}.md. frontmatter description ≤ 512 / when_to_use ≤ 128 / 加 arguments.

## 已知
L4-inbox → L1/L2/L3 + 项目/领域 路由. 默认入口 L3-short. 升级方向 = 抗遗忘 (L3→L2→L1→L0).
路由 8 顺序: domain area → URL → L0 关键词 (ask) → L1/L2/L3 关键词 → 默认 L3 → 复用 ≥3 promote-L2 标 → 复用 ≥5+w≥0.8 promote-L1 标.

## frontmatter arguments
arguments:
  - name: mode
    description: "--dry-run 计划 (默认) / --apply 落盘"
    required: false
    type: enum
    values: ["--dry-run", "--apply"]
  - name: target
    description: "vault 根路径, 默认 ~/.cortex"
    required: false
    type: path
argument-hint: "[--dry-run|--apply] [target]"

## SKILL.md 内容
1. frontmatter
2. 1 段总览 (L4-inbox → 项目/领域/L3 默认入口)
3. 路由速查表 (顺序/信号/目标/模式 — 8 行精简)
4. 路由表:
   | 任务 | 文件 |
   | 查三轴 + 8 顺序决策 | references/classifier.md |
   | 查游标 + JSON 格式 + apply 行为 | references/io.md |
   | 查 extract.sh 入口 + 示例 + L0 mock | references/usage.md |

## references 内容
- classifier.md: 三轴信号源 + 8 顺序路由判定表 + 路径名后缀防写反提醒
- io.md: state/extract-cursor.json 结构 + dry-run JSON plan 字段 + apply 行为 (mkdir / 同名 .N / archive 不 delete)
- usage.md: extract.sh --help 完整文档 + 4 类调用示例 (dry-run / apply / project-level / --no-cursor) + CORTEX_EXTRACT_L0_AUTO env mock

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-extract/**

## 验收
subtask "验证" 节全过.

## 失败处理
- 工具错 → 重试 1 次
- 字符上限 → 砍到 references, 保触发词 (extract/提取/promote/整理/归档/inbox/digest)

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-extract/
```
