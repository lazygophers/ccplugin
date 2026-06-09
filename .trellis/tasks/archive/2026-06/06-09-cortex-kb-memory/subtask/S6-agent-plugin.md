---
id: S6
slug: agent-plugin
deliverable: D6
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: main
isolation: none
depends-on: [S4, S5]
blocks: [S7]
estimated-tokens: 6000
---

# S6 · 改写 cortex agent + plugin.json 注册

## 目标

把 cortex 主 agent 改成协调 4 skill 的代理, 同步更新 plugin.json 注册 4 skill + 1 agent, 删除骨架占位 skill, 更新 README/llms.txt 描述。

## 产出

- `plugins/tools/cortex/agents/cortex.md` (改写, 不再是 TODO 占位)
- `plugins/tools/cortex/.claude-plugin/plugin.json` (skills 数组 4 项, agents 数组 1 项, description 正式)
- `plugins/tools/cortex/skills/cortex/` (删除骨架占位目录)
- `plugins/tools/cortex/README.md` (描述 4 skill + agent + 目录契约)
- `plugins/tools/cortex/llms.txt` (同步更新)

## 验证

```bash
# JSON 校验
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 4, f\"skills={d['skills']}\"
assert len(d['agents']) == 1
assert 'TODO' not in d['description']
print('OK')
"

# Skill 目录全在
for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
  test -d plugins/tools/cortex/skills/$s/ || echo "MISSING: $s"
done

# 骨架占位已删
test ! -d plugins/tools/cortex/skills/cortex/ || echo "leftover skeleton"

# Agent frontmatter
python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/agents/cortex.md').read().split('---')[1])
assert fm['name'] == 'cortex'
assert 'TODO' not in fm['description']
assert fm.get('tools') and fm.get('model')
print('OK')
"

# README/llms.txt 已去 TODO
! grep -q '^# cortex' plugins/tools/cortex/README.md ; ! grep -q 'TODO:' plugins/tools/cortex/README.md
```

## 资源

- 独占文件 (与所有人互斥): `plugins/tools/cortex/.claude-plugin/plugin.json`
- 写: `plugins/tools/cortex/agents/cortex.md` `plugins/tools/cortex/README.md` `plugins/tools/cortex/llms.txt`
- 删: `plugins/tools/cortex/skills/cortex/`
- 审批槽位: 是 (本 subtask 后立即进 G1)

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S4 | `skills/cortex-lint/SKILL.md` 存在 | 文件检测 |
| S5 | `skills/cortex-extract/SKILL.md` 存在 | 文件检测 |
| (隐式) S2 / S3 | 同上 | 文件检测 |

## 执行细节

1. **agent**: 改写 `agents/cortex.md`:
   ```yaml
   ---
   name: cortex
   description: cortex 主代理 - 协调 schema-knowledge / schema-memory / lint / extract 4 skill, 维护 ~/.cortex/.wiki/ 与 <repo>/.wiki/ 知识库 + 记忆系统
   tools: Read, Write, Edit, Glob, Grep, Bash
   model: inherit
   permissionMode: default
   ---
   ```
   主体: 角色 / 边界 (只读 .trellis/, 写仅限 ~/.cortex 与 <repo>/.wiki) / 4 skill 调度策略 / 输入输出契约 / 失败处理
2. **plugin.json**:
   ```json
   {
     "description": "cortex - 知识库 + 记忆管理插件: 双层同构 (~/.cortex/.wiki + <repo>/.wiki), 5 级记忆 (L0-L4), 3 模块知识库 (projects/domains/scripts), lint + extract 自动化",
     "skills": [
       "./skills/cortex-schema-knowledge",
       "./skills/cortex-schema-memory",
       "./skills/cortex-lint",
       "./skills/cortex-extract"
     ],
     "agents": ["./agents/cortex.md"],
     "keywords": ["cortex","knowledge-base","memory","vault","obsidian","wiki","lint","extract","L0","L1","L2","L3","L4"]
   }
   ```
3. **删占位**: `rm -rf plugins/tools/cortex/skills/cortex/`
4. **README**: 补 4 skill + agent 表 + 目录契约链接 (`docs/layout.md`) + 触发示例
5. **llms.txt**: 同步, 目录树更新

## 回滚

- 触发条件: plugin.json JSON 错 / agent frontmatter 错
- 步骤:
  ```bash
  git checkout plugins/tools/cortex/.claude-plugin/plugin.json plugins/tools/cortex/agents/cortex.md plugins/tools/cortex/README.md plugins/tools/cortex/llms.txt
  test -d plugins/tools/cortex/skills/cortex/ || git checkout plugins/tools/cortex/skills/cortex/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| plugin.json 改坏导致整个插件加载失败 | 用户不能用 | git checkout 回滚到 commit 版本; 改前先 `python3 -m json.tool` 验证 |
| 删 skills/cortex/ 后骨架追溯困难 | 历史不可见 | 通过 git log 找回; commit 信息标"取代骨架占位" |
| agent description 触发词与 skill description 冲突 | skill 不命中 | agent 描述只列"协调", 触发词留给各 skill |

## 历史

- 2026-06-09: created
