---
id: S3
slug: lint
deliverable: D3,D5
parent-task: 06-09-cortex-skills-multifile
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S5]
estimated-tokens: 8000
---

# S3 · 拆 cortex-lint 为多文件

## 产出

- `skills/cortex-lint/SKILL.md` (覆盖, ≤ 60 行)
- `references/rules.md` (R1-R7 详情)
- `references/fixers.md` (R2 推断 + R4 mkdir + 实现位置 lint.sh + _lint/)
- `references/output.md` (输出格式 + fixture + 验证)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-lint
test -f $d/SKILL.md && [[ $(/usr/bin/find $d/references -name '*.md' | wc -l | tr -d ' ') -ge 3 ]]
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-lint'
assert len(fm['description']) <= 512
wtu = fm['when_to_use'] if isinstance(fm['when_to_use'], str) else '/'.join(fm['when_to_use'])
assert len(wtu) <= 128
assert fm.get('arguments') and len(fm['arguments']) >= 2
print('OK')
"
```

## 资源

独占 `skills/cortex-lint/**`.

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-skills-multifile

## 目标
拆 cortex-lint SKILL.md 单文件 → SKILL.md (≤ 60 行) + references/{rules,fixers,output}.md. frontmatter description ≤ 512 / when_to_use ≤ 128 / 加 arguments.

## 已知
7 规则: R1 wikilink (warn) / R2 frontmatter (error,fix) / R3 命名 (warn) / R4 同构 (error,fix) / R5 孤儿 (warn) / R6 等级语义 (error) / R7 脚本目录用途分离 (warn).
路径全用中文三模块 (项目/领域/脚本).

## frontmatter arguments
arguments:
  - name: mode
    description: "--check 仅检查 (默认) / --fix 落盘修复"
    required: false
    type: enum
    values: ["--check", "--fix"]
  - name: target
    description: "vault 根路径, 默认 ~/.cortex"
    required: false
    type: path
argument-hint: "[--check|--fix] [target]"

## SKILL.md 内容
1. frontmatter
2. 1 段总览
3. 7 规则速查表 (ID/规则/级别/autofix)
4. 路由表:
   | 任务 | 文件 |
   | 查 7 规则具体定义 | references/rules.md |
   | 查 R2/R4 fixer 行为 + 实现 | references/fixers.md |
   | 查输出格式 + fixture + 验证 | references/output.md |
5. 入口命令一行: bash scripts/lint.sh [--check|--fix] --target <dir>

## references 内容 (从源 SKILL.md 抄移, 不丢失)
- rules.md: R1-R7 每个 (定义 + level + 是否 autofix + 检测策略)
- fixers.md: R2 推断表 (路径前缀→type, 路径段→area/level) + R4 mkdir + 实现位置 (lint.sh ≤ 80 行入口 + _lint/runner.py + rules.py + fixers.py + __init__.py)
- output.md: stdout 格式 + stderr 详情格式 + fixture 文件清单 + 验证命令

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-lint/**

## 验收
subtask "验证" 节全过.

## 失败处理
- 工具错 → 重试 1 次
- 字符上限超 → 砍到 references, 保触发词 (lint/校验/体检/audit/死链/孤儿/规范化/frontmatter)

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-lint/
```
