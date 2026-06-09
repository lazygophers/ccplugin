---
id: S2
slug: context-skill
deliverable: D2,D4
parent-task: 06-09-cortex-digest-skills
execution-layer: sub-agent
estimated-tokens: 7000
---

# S2 · 建 cortex-context-digest skill

## 产出

- `skills/cortex-context-digest/SKILL.md` ≤ 60 行
- `skills/cortex-context-digest/references/scope.md` (全局 vs 项目级 自动判定 + --scope 显式)
- `skills/cortex-context-digest/references/triggers.md` (识别值得 digest 的内容: 决策/选型/踩坑/规则)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-context-digest
test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]]
test -f $d/references/scope.md && test -f $d/references/triggers.md
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-context-digest'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str) and fm.get('user-invocable') is True
print('OK')
"
# scope 关键概念存在
grep -q 'global\|全局' $d/references/scope.md
grep -q 'project\|项目' $d/references/scope.md
grep -q '--scope' $d/references/scope.md
```

## Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-digest-skills

## 目标
建 cortex-context-digest skill (SKILL.md ≤ 60 行 + 2 references). 不写脚本. skill 步骤指导 main 会话整理当前上下文 → 记忆库 (自动判定全局 vs 项目级, 或用户 --scope 强制).

## 已知
- frontmatter:
  name: cortex-context-digest
  description: "整理当前会话上下文 → 记忆库. 自动判定全局 (L0 关键词/跨项目语义) vs 项目级 (默认/含 repo 特定); 用户可 --scope global|project 显式覆盖. 复用 cortex-extract 三轴 + cortex-schema 路径. 任务收尾或显式 'digest 上下文/沉淀' 触发."
  when_to_use: "整理上下文/沉淀本次会话/digest context/任务收尾沉淀/把决策落记忆库/全局还是项目级判定"
  argument-hint: "[--scope global|project] [--dry-run|--apply]"
  arguments: "[--scope 全局|项目] [--dry-run|--apply]"
  user-invocable: true

## scope 判定规则 (优先序)
1. --scope global → 全局
2. --scope project → 项目级
3. 自动: 含 L0 触发词 (永远/硬性/never/严禁/绝不) → 全局
4. 自动: 引用当前 repo 名/路径/具体文件 → 项目级
5. 自动: 跨项目通用 (shell/AI 协作通则) → 全局
6. 兜底 → 项目级 (保守)

## SKILL.md 结构
1. frontmatter
2. 1 段总览 (上下文整理 → 记忆库 + scope 自动)
3. 6 步执行流程概览 (Read 任务上下文 → 识别增量 → scope 判定 → 调 extract --dry-run → 用户审 → --apply)
4. 路由表: scope.md / triggers.md
5. 引用 cortex-schema/extract/save

## references
- scope.md: 6 优先序 + 各规则举例 + --scope 显式语义 + 默认保守 project 原因
- triggers.md: 什么值得 digest (决策/选型/踩坑/规则/L0 候选) + 不该 digest (临时 fix/调试输出/会话客套) + 提取格式 (frontmatter + 正文)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-context-digest/** (新建)
禁改: 其他

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```
