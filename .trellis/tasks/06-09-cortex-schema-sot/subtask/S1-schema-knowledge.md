---
id: S1
slug: schema-knowledge-absorb
deliverable: D1
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S3, S4, S5, S6]
estimated-tokens: 10000
---

# S1 · schema-knowledge 吸收 layout.md (knowledge 部分)

## 目标

把 `docs/layout.md` 中所有 knowledge / 物理布局 / 同构 / 脚本用途 / 开放扩展 / frontmatter 通用 / 模板 相关内容迁入 `cortex-schema-knowledge` skill, 让其成为唯一真相源.

## 产出

- `skills/cortex-schema-knowledge/references/topology.md` (新, ~/.cortex/ 顶层布局 + 双层同构 + 开放扩展位 + 必备目录清单)
- `skills/cortex-schema-knowledge/references/templates.md` (新, frontmatter 通用字段表 + 各 type 模板 project/domain/rule/memory/vault-script)
- 既有 references/{projects,domains,scripts}.md 补充: 引用 topology.md 处用 markdown link, 不再重复物理树
- SKILL.md 路由表追加 topology / templates 两行

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema-knowledge
test -f $d/references/topology.md && test -f $d/references/templates.md
# 顶层布局完整 (含 5 必备目录 + 双层同构 + 开放扩展)
grep -q 'config' $d/references/topology.md
grep -q '同构' $d/references/topology.md
grep -q '开放扩展' $d/references/topology.md
# 模板有 ≥ 4 个 type
grep -q 'type: project' $d/references/templates.md
grep -q 'type: domain' $d/references/templates.md
grep -q 'type: rule' $d/references/templates.md
grep -q 'type: memory\|type: vault-script' $d/references/templates.md
# SKILL.md 路由表含新两项
grep -q 'topology.md' $d/SKILL.md
grep -q 'templates.md' $d/SKILL.md
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert len(fm['description']) <= 512 and (len(fm['when_to_use']) if isinstance(fm['when_to_use'], str) else len('/'.join(fm['when_to_use']))) <= 128
assert '用户说' not in fm['description'] and '用户说' not in str(fm['when_to_use'])
print('OK')
"
```

## 资源

独占 `skills/cortex-schema-knowledge/**`. 读 `docs/layout.md` (源).

## 执行细节

1. Read `docs/layout.md` 全文
2. 抽出归 knowledge 的内容:
   - `~/.cortex/` 顶层布局 (.wiki / config / state / scripts / logs + 开放扩展)
   - `<repo>/.wiki/` 物理树
   - 双层同构原则
   - 脚本目录用途分离表 (顶层 scripts/ vs .wiki/脚本/)
   - frontmatter 通用字段表 (type/level/created/updated/tags/aliases/weight/source/area/mindmap)
3. 写 `references/topology.md`:
   - 顶层物理树 ASCII (来自 layout.md "用户级根" 章节)
   - 项目级物理树
   - 双层同构原则段
   - 开放扩展位说明
   - 脚本用途分离表
   - validate-layout.sh 校验的必备目录清单 (与 schema-knowledge 三模块 + topology 顶层结合)
4. 写 `references/templates.md`:
   - 通用 frontmatter 字段表 (从 layout.md "frontmatter 通用字段" 抄)
   - 各 type 完整 frontmatter 模板:
     - project (README.md): 取自 projects.md 已有示例
     - domain: 取自 domains.md
     - rule (L0): 写新模板
     - memory (L1/L2/L3): 写新模板
     - vault-script: 取自 scripts.md
5. 改 SKILL.md (≤ 60 行) 路由表:
   ```
   | 任务 | 文件 |
   | 查 ~/.cortex 顶层物理布局 / 双层同构 / 必备目录 / 开放扩展 | references/topology.md |
   | 查 frontmatter 通用字段 / 各 type 模板 | references/templates.md |
   | 入库 GitHub / GitLab / Website | references/projects.md |
   | 写或整理领域笔记 | references/domains.md |
   | vault 内部脚本 / 用户操作入口 / 混用检测 | references/scripts.md |
   ```
6. 既有 projects.md / domains.md / scripts.md 内若与 topology / templates 重复, 改为引用 `(物理树详见 ../topology.md)`

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-sot

## 目标
让 cortex-schema-knowledge 成为目录结构 / 路径规范 / 文件模板的唯一真相源. 吸收 docs/layout.md 中所有 knowledge / 物理布局 / 同构 / 脚本用途 / 开放扩展 / frontmatter 通用 / 模板 相关内容. 新增 references/topology.md + references/templates.md.

## 已知
- 源文件: plugins/tools/cortex/docs/layout.md (必读全文)
- 现有 references: projects.md / domains.md / scripts.md
- 三模块中文目录名 (项目/领域/脚本) + 5 级英文 (L0-core ... L4-inbox) 路径名不变
- 脚本目录用途分离: 顶层 scripts/ (英文, 用户入口, 仅用户级) vs .wiki/脚本/ (中文, vault 内部, 双层)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-schema-knowledge/**
禁改: docs/layout.md (S5 删) / 其他 skill / 脚本 / agent

## 输出
- references/topology.md ≤ 220 行
- references/templates.md ≤ 220 行
- SKILL.md ≤ 60 行 (仅追加路由表两行)
- projects.md / domains.md / scripts.md 内重复物理树改为引用 topology.md

## 验收
subtask 验证节命令全过.

## 失败处理
- 工具瞬时错误 → 重试 1 次
- 字符上限超 → 拆 references 或砍冗余
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-schema-knowledge/
```
