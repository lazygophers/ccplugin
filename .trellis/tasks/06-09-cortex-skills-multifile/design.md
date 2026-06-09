# Design — cortex skills 多文件改造

## 目标结构 (每个 skill)

```
skills/<skill-name>/
├── SKILL.md                ← 薄入口 (≤ 60 行)
│   - frontmatter (含 arguments)
│   - 1 段 ≤ 10 行总览
│   - 路由表: 何时读哪个 reference
│   - 速查图/表 (可选, 关键决策)
└── references/
    ├── <logical-block-1>.md
    ├── <logical-block-2>.md
    └── <logical-block-3>.md (按需)
```

## 各 skill 拆分计划

### cortex-schema-knowledge → 3 reference

| 文件 | 内容 |
| --- | --- |
| `SKILL.md` | frontmatter + 三模块速查表 + 路由表 |
| `references/projects.md` | 项目模块 (路径 / host 枚举 / frontmatter / 命名) |
| `references/domains.md` | 领域模块 (路径 / area 预设 / frontmatter / 示例 / 禁路径) |
| `references/scripts.md` | 脚本模块 (vault 内部 + 用户操作入口 + 混用检测) |

### cortex-schema-memory → 3 reference

| 文件 | 内容 |
| --- | --- |
| `SKILL.md` | frontmatter + 反直觉等级速查图 + 路由表 |
| `references/levels.md` | L0-L4 五段 (定义/路径/写入触发/迁移) |
| `references/axes-routing.md` | 三轴 (抗遗忘度/强度/复用面) + extract 路由表 |
| `references/properties.md` | 关键性质 (默认 L3 入口 / promote 离线 / forget 不自动删) |

### cortex-lint → 3 reference

| 文件 | 内容 |
| --- | --- |
| `SKILL.md` | frontmatter + 7 规则速查表 + 路由表 |
| `references/rules.md` | 7 规则详情 (R1-R7) |
| `references/fixers.md` | R2 推断规则 + R4 mkdir + 实现 (lint.sh + _lint/) |
| `references/output.md` | 输出格式 + fixture 说明 + 验证命令 |

### cortex-extract → 3 reference

| 文件 | 内容 |
| --- | --- |
| `SKILL.md` | frontmatter + 路由速查表 + 路由表 |
| `references/classifier.md` | 三轴信号源 + 决策表 (8 顺序) |
| `references/io.md` | 增量游标 + dry-run JSON + apply 行为 |
| `references/usage.md` | extract.sh 入口 + 调用示例 + L0 mock env |

## frontmatter 长度约束 (新)

- `description` ≤ 512 字符 (单行或紧凑短句; 描述功能 + 关键触发词)
- `when_to_use` ≤ 128 字符 (**不再用 yaml list**, 改为单行短句 / 短语集合, 用 `/` 或 `;` 分隔)
- 检测: `python3 -c "import yaml; fm = yaml.safe_load(open(...).read().split('---')[1]); assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128"`

## frontmatter `arguments` 字段规范

```yaml
arguments:
  - name: <param-name>
    description: <参数描述>
    required: <true | false>
    type: <string | enum | path | flag>  # 可选
    values: [<list>]  # 仅 enum 时填
```

对应当前各 skill 的 `argument-hint`:

| skill | argument-hint | arguments |
| --- | --- | --- |
| cortex-schema-knowledge | `[module]` | `[{name: module, description: "项目 \| 领域 \| 脚本, 限定查 schema 的子模块, 不填则全部", required: false, type: enum, values: [项目, 领域, 脚本]}]` |
| cortex-schema-memory | `[level]` | `[{name: level, description: "L0 \| L1 \| L2 \| L3 \| L4, 限定查特定级别, 不填则全部", required: false, type: enum, values: [L0, L1, L2, L3, L4]}]` |
| cortex-lint | `[--check\|--fix] [target]` | `[{name: mode, description: "--check 仅检查 (默认) / --fix 落盘修复", required: false, type: enum, values: [--check, --fix]}, {name: target, description: "vault 根路径 (默认 ~/.cortex)", required: false, type: path}]` |
| cortex-extract | `[--dry-run\|--apply] [target]` | `[{name: mode, description: "--dry-run 计划 (默认) / --apply 落盘", required: false, type: enum, values: [--dry-run, --apply]}, {name: target, description: "vault 根路径 (默认 ~/.cortex)", required: false, type: path}]` |

## SKILL.md 路由表模板

```markdown
## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 <场景 A> | `references/<file-a>.md` |
| 查 <场景 B> | `references/<file-b>.md` |
| 查 <场景 C> | `references/<file-c>.md` |
```

## 资源边界

| Subtask | 写资源 | 互斥 |
| --- | --- | --- |
| S1 | `skills/cortex-schema-knowledge/**` | 无 (独立目录) |
| S2 | `skills/cortex-schema-memory/**` | 无 |
| S3 | `skills/cortex-lint/**` | 无 |
| S4 | `skills/cortex-extract/**` | 无 |
| S5 | 只读 (验证) | 与所有等待 |

4 拆分完全并行.

## 验证契约

| Subtask | 验证 |
| --- | --- |
| S1-S4 | `ls skills/<skill>/{SKILL.md,references/}`; SKILL.md ≤ 60 行; references ≥ 2 文件; frontmatter 含非空 arguments; `len(description) ≤ 512`; `len(when_to_use) ≤ 128` |
| S5 | 4 skill 全过上述检查; 内容完整性 (源 SKILL.md 关键 token 全部出现在新结构中) |

## Rollback

每 skill 独立, 失败仅回滚该 skill 目录:
```bash
git checkout plugins/tools/cortex/skills/<skill-name>/
```
