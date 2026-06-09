---
id: S2
slug: schema-knowledge
deliverable: D2
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: sub-agent
isolation: none
depends-on: [S1]
blocks: [S4, S5, S6]
estimated-tokens: 10000
---

# S2 · 写 cortex-schema-knowledge skill

## 目标

落一份知识库目录结构契约 skill, 把 projects / domains / scripts 三模块的路径规则、frontmatter schema、命名约定写成可被主会话加载并触发的 skill 文档。

## 产出

- `plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md` — skill 主文档
- frontmatter 含: `name: cortex-schema-knowledge`, `description` (前置触发词), `when_to_use`, `argument-hint`
- 主体三段: 项目模块 / 领域模块 / 脚本模块, 各含路径规则 + frontmatter schema + 命名 + 示例

## 验证

```bash
test -f plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md
python3 -c "
import yaml
c = open('plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md').read()
fm = yaml.safe_load(c.split('---')[1])
assert fm['name'] == 'cortex-schema-knowledge'
assert fm['description'] and len(fm['description']) > 20
assert fm['when_to_use']
print('OK')
"
grep -q '^## .*[项目|projects]' plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md
grep -q '^## .*[领域|domains]' plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md
grep -q '^## .*[脚本|scripts]' plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md
```

期望: 全部退出 0; YAML 校验输出 "OK"。

## 资源

- 独占文件: `plugins/tools/cortex/skills/cortex-schema-knowledge/**`
- 与 S3 不互斥 (不同子目录)
- 审批槽位: 否 (Gate 在 S6 后统一)

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S1 | `docs/layout.md` 存在 | 文件检测 |

## 执行细节

skill 主体按 design.md "契约: 知识库三模块路径规则" 表展开:

1. **项目模块** (projects/):
   - 路径: `<root>/projects/<host>/<owner>/<repo>/` (root = ~/.cortex/.wiki 或 <repo>/.wiki)
   - host 枚举: github.com / gitlab.com / 其他 domain
   - 用例区分: GitHub/GitLab repo vs Website (用 `source` URL 区分)
   - frontmatter: `type: project` `source: <URL>` `summary: <一句话>` `mindmap: <canvas 相对路径>` `graph: <可选 graph 文件路径>`
   - 子内容: 摘要 README 文件 + 可选 mindmap.canvas + 可选 graph.json
2. **领域模块** (domains/):
   - 路径: `<root>/domains/<area>/<sub>/[<sub2>/]<topic>.md`
   - 至少二级 (area + sub), 鼓励三级
   - area 预设: `tech` `life` `finance` (用户可扩展)
   - frontmatter: `type: domain` `area: tech` `tags: [<list>]` `aliases: [<list>]`
3. **脚本模块** (scripts/) — 知识库内部脚本 (vault-internal):
   - 用户级: `~/.cortex/.wiki/scripts/<name>.{sh,py}`
   - 项目级: `<repo>/.wiki/scripts/<name>.{sh,py}`
   - 用途: 被 lint / extract / canvas 生成等流程调用的内部工具, 不是给用户在 shell 直接调的
   - 命名: kebab-case
   - sh: shebang + 5 行内 help text
   - py: 模块 docstring + `if __name__ == "__main__":` 入口
4. **(补充, 不属知识库三模块)** 用户操作入口脚本: `~/.cortex/scripts/<name>.{sh,py}`
   - 用户从 shell 直接调的 CLI / 包装器, 鼓励 `cortex-` 前缀 (如 `cortex-save`, `cortex-recall`)
   - **仅用户级**, 项目级不设
   - 不进 knowledge 模块校验范围 (lint 单独治理)
   - skill 文档要明确"这一类不属 knowledge 三模块", 防止下游脚本误把它当 vault 内部脚本处理

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-kb-memory

## 目标
写 cortex-schema-knowledge skill (产出节列出的文件), 严格按 design.md "契约: 知识库三模块路径规则" 表 + 本 subtask 文件 "执行细节" 三段展开。

## 已知
- 上游: docs/layout.md 已存在 (S1 产出)
- 三模块: projects / domains / scripts (后者 = vault 内部脚本)
- 双层同构: ~/.cortex/.wiki/ 与 <repo>/.wiki/
- 区分: `~/.cortex/.wiki/scripts/` = vault 内部脚本 (属三模块); `~/.cortex/scripts/` = 用户操作入口 CLI (不属三模块, 仅用户级)

## 工作目录与范围
- cwd: /Users/luoxin/persons/lyxamour/ccplugin
- 可改文件: plugins/tools/cortex/skills/cortex-schema-knowledge/**
- 禁改: 其他 plugins/tools/cortex/ 内容; .trellis/**; ~/.cortex/**

## 输出格式
- 类型: 新文件
- 行数上限: SKILL.md ≤ 200 行

## 验收标准
跑 subtask 文件 "验证" 节列出的全部命令, 都通过。

## 失败处理
- 工具瞬时错误 → 重试 1 次
- frontmatter 字段拿不准 → 输出 "需要: <问题>" 回 main
- 资源不可用 → Blocked, 不重试

## Sub-agent 自防护
已是 trellis-implement, 直接做, 禁再 spawn trellis-implement / trellis-check。
```

## 回滚

- 触发条件: frontmatter YAML 不合法 或 触发词覆盖不到典型用法
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/skills/cortex-schema-knowledge/
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| description 触发词不够具体, skill 加载漏命中 | 用户输入"知识库结构"未触发 | when_to_use 列 ≥ 8 短语 (项目入库 / 领域归档 / 知识库目录 / vault schema 等) |
| 三模块 frontmatter schema 与既有 obsidian vault 不兼容 | 旧数据迁移成本高 | 字段尽量复用 (type/tags/aliases), 新字段 (source/mindmap) 仅在 cortex 域内强制 |

## 历史

- 2026-06-09: created
