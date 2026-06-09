# Design — cortex-schema 模板按变体拆分

## 拆分映射 (source → target)

旧 `references/templates.md` 单文件 → 10 新文件:

| 旧段 | 新文件 | 内容来源 |
| --- | --- | --- |
| `## type: project` (github 示例) | `templates/project/github.md` | 现有 yaml + 引 examples/project.md |
| (新, github 同结构, host=gitlab.com) | `templates/project/gitlab.md` | 仿 github 块, source 改 https://gitlab.com/ ... |
| (新, host=任意 website) | `templates/project/website.md` | 仿 github, source 任意 URL, owner=`_` 或 `_`, 提示对其他 domain 适用 |
| `## type: domain` | `templates/domain.md` | 现有 yaml + 引 examples/domain.md |
| `## type: rule` | `templates/memory/L0-rule.md` | 现有 yaml + 引 examples/rule.md |
| `## type: memory` (L1 块) | `templates/memory/L1-long.md` | 现有 + 引 examples/memory-L1.md |
| `## type: memory` (L2 块) | `templates/memory/L2-mid.md` | 现有 + 引 examples/memory-L2.md |
| `## type: memory` (L3 块) | `templates/memory/L3-short.md` | 现有 + 引 examples/memory-L3.md |
| `## type: memory` (L4 块) | `templates/memory/L4-inbox.md` | 现有 + 标 "无独立 example, 参照 memory-L3.md 形态" |
| `## type: vault-script` | `templates/vault-script.md` | 现有 bash 注释块 + (补) py docstring 块 + 引 examples/vault-script.md |
| 通用字段表 | (合 SKILL.md 或新 templates/_fields.md) | 不分散; 选 templates/_fields.md 作公共字段定义 |
| 引用段 | (废, 各 template 内自引) | — |

通用字段表归属决定:
- 选项 A: 每个 template 重复字段表 (冗余)
- 选项 B: `templates/_fields.md` (新文件, 公共字段)
- 选项 C: 留在 SKILL.md (但 ≤ 60 行难放)

**选 B**: `templates/_fields.md` (下划线前缀表示"非 type 文件, 是公共片段").

最终: templates/ = 10 type 文件 + 1 `_fields.md` = 11 文件.

## 每个模板文件结构

```markdown
> 模板 — type=X[, level=Y] [, variant=Z]; 完整样例见 <examples/<type>.md 或 参照说明>

## 必备 / 推荐字段

(简短说明本变体的关键字段, 引 _fields.md 看全字段)

## frontmatter 块

```yaml
---
type: ...
...
---
```

## 备注

- 特殊说明 (如 L4-inbox 无 weight, github 必须 owner/repo 段)
- 引用: examples/<type>.md / 同 type 其他变体
```

## SKILL.md 路由表 (更新)

```
| 任务 | 文件 |
| 查 ~/.cortex 顶层物理布局 / 同构 / 必备目录 / 详细 ASCII | references/topology.md |
| 查三模块路径规则 + 命名 + frontmatter | references/knowledge-modules.md |
| 查 5 级记忆语义 / 映射 / 反写防呆 / 遗忘曲线 | references/memory-levels.md |
| 查 frontmatter 模板 (按 type + 变体) | templates/ (含 memory/ project/ + domain.md + vault-script.md) |
| 查完整 .md 样例 | examples/<type>.md |
```

通用字段表用一行: `查 frontmatter 通用字段表 | templates/_fields.md`

## references 更新

- `references/templates.md` 删除
- `references/knowledge-modules.md` 内引用从 `templates.md` 改成 `../templates/<path>.md` 对应变体
- `references/memory-levels.md` 内引用从 `templates.md` 改成 `../templates/memory/<level>-<suffix>.md`
- `references/topology.md` 内引用同步

## 资源边界

| Subtask | 写资源 |
| --- | --- |
| S1 | `templates/**` (新建 11 文件) + 删 `references/templates.md` |
| S2 | `SKILL.md` + `references/{topology,knowledge-modules,memory-levels}.md` 引用更新 |
| S3 | 只读验证 + 暂存 |

S1 → S2 → S3 串行.

## 验证

- 11 文件存在
- 每文件 ≤ 50 行
- 每文件含 `---` frontmatter 块 + (除 `_fields.md` 外) 至少 1 处 `examples/` 或 "参照" 引用
- references 内 0 `references/templates.md` 残留
- SKILL.md ≤ 60 行
- smoke (validate / lint / extract) 同前
