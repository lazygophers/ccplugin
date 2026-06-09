---
id: S1
slug: schema-knowledge
deliverable: D1,D5
parent-task: 06-09-cortex-skills-multifile
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S5]
estimated-tokens: 8000
---

# S1 · 拆 cortex-schema-knowledge 为多文件

## 目标

把 `skills/cortex-schema-knowledge/SKILL.md` 拆成 SKILL.md (≤ 60 行薄入口) + references/{projects,domains,scripts}.md, 同时补 frontmatter `arguments` + 收紧 `description` ≤ 512 + `when_to_use` ≤ 128.

## 产出

- `skills/cortex-schema-knowledge/SKILL.md` (覆盖)
- `skills/cortex-schema-knowledge/references/projects.md` (项目模块)
- `skills/cortex-schema-knowledge/references/domains.md` (领域模块)
- `skills/cortex-schema-knowledge/references/scripts.md` (脚本模块 + 用户入口补充)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema-knowledge
test -f $d/SKILL.md
test -f $d/references/projects.md
test -f $d/references/domains.md
test -f $d/references/scripts.md
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-schema-knowledge'
assert len(fm['description']) <= 512
wtu = fm['when_to_use']
wtu = wtu if isinstance(wtu, str) else '/'.join(wtu)
assert len(wtu) <= 128
assert fm.get('arguments') and len(fm['arguments']) >= 1
print('OK')
"
```

## 资源

- 独占: `skills/cortex-schema-knowledge/**`
- 与其他 S 不互斥

## 执行细节

1. Read 当前 `SKILL.md` (信息源)
2. 删原 SKILL.md
3. 写新 SKILL.md (薄):
   - frontmatter (含 arguments 按 design.md 表)
   - 1 段 ≤ 10 行总览 (三模块 + 双层同构)
   - 三模块速查表 (模块/用户级路径/项目级路径/type)
   - 路由表: "查项目模块 → projects.md / 查领域 → domains.md / 查脚本 → scripts.md"
   - 引用 docs/layout.md 作权威
4. 拆 references/:
   - `projects.md`: 项目模块全部内容 (路径规则, host 枚举, frontmatter 示例, 命名约定)
   - `domains.md`: 领域模块全部 (路径, area 预设, frontmatter 示例, 禁路径)
   - `scripts.md`: 脚本模块 (vault 内部) + 用户操作入口脚本补充 + 混用检测

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-skills-multifile

## 目标
把 plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md (当前单文件) 拆成 SKILL.md (≤ 60 行) + references/{projects,domains,scripts}.md 三个 reference 文件。同时改 frontmatter:
- description ≤ 512 字符 (扁平字符串)
- when_to_use ≤ 128 字符 (改成单行短句, 不再用 yaml list 多行)
- 新增 arguments 字段 (列表)

## 已知
- 单文件源: plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md
- 三模块: 项目 / 领域 / 脚本 (中文路径)
- 同构: ~/.cortex/.wiki/ + <repo>/.wiki/
- 模板参照: trellisx-orchestrate skill (主 SKILL.md + references/)

## frontmatter arguments
arguments:
  - name: module
    description: "项目 | 领域 | 脚本, 限定查 schema 子模块, 不填则全部"
    required: false
    type: enum
    values: [项目, 领域, 脚本]

argument-hint: "[module]" (保持)

## SKILL.md 模板
1. frontmatter (上)
2. 1 段总览: "知识库 schema — 项目/领域/脚本 三模块路径规则与 frontmatter 契约. 双层同构 (~/.cortex/.wiki + <repo>/.wiki)."
3. 速查表 (4 列: 模块 | 用户级 | 项目级 | type)
4. ## 何时读哪个 reference
   | 任务 | 文件 |
   | --- | --- |
   | 入库 GitHub/GitLab/Website | references/projects.md |
   | 写领域笔记 | references/domains.md |
   | vault 内部脚本 / 用户操作入口 | references/scripts.md |
5. ## 引用: docs/layout.md (权威)

## 工作目录与范围
- cwd: /Users/luoxin/persons/lyxamour/ccplugin
- 可改: plugins/tools/cortex/skills/cortex-schema-knowledge/** (重写整目录)
- 禁改: 其他文件

## 输出格式
- SKILL.md ≤ 60 行
- 每个 reference ≤ 200 行

## 验收
subtask 验证节命令全过, 输出 OK.

## 失败处理
- 工具错 → 重试 1 次
- 内容截断 → 检查 description 512 / when_to_use 128 字符上限
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-schema-knowledge/
```

## 风险

| 风险 | 缓解 |
| --- | --- |
| description/when_to_use 砍后丢触发词 | 优先保 "知识库/vault/项目/领域/脚本/schema/入库" 关键词 |
| 三模块内容不平衡 | scripts.md 最长 (含双重内容) 允许达 200 行 |
