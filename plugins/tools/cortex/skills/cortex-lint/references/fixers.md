# Fixer 实现 (R2 / R4) + 代码位置

## R2 frontmatter 推断规则

按 `cortex-schema` 三模块路径前缀 + `cortex-schema` 5 级 level 段判定 type / 衍生字段。

| 缺失字段 | 推断来源 |
| --- | --- |
| `type` | 按路径前缀匹配三模块 / memory 5 级 → 对应 type (映射权威见 `cortex-schema/references/knowledge-modules.md` + `cortex-schema/references/memory-levels.md`) |
| `area` (domain) | 领域模块路径中模块根之后的首段 |
| `level` (rule/memory) | memory 路径段中 `L([0-4])-` 提取 (反写禁止, 见 memory-levels.md) |
| `created` | 文件 mtime (ISO date) |
| `source` (project) | 留空占位 `TODO: fill source URL` (用户必须手填) |

frontmatter 字段全集与各 type 模板见 `cortex-schema/references/templates.md`。

写回策略: 保留原 frontmatter 顺序与注释, 仅在末尾追加缺失字段; 如原文件无 frontmatter, 则在文件最顶补一段 `---\n...\n---\n`。

## R4 mkdir 修复

对缺失目录直接 `os.makedirs(path, exist_ok=True)`, 不写占位文件。

待补清单由权威源拼出:

- 顶层 + 三模块必备目录 → `cortex-schema/references/topology.md`
- memory 5 级必备目录 → `cortex-schema/references/memory-levels.md`

Fixer 在运行时拼接清单, 不在本文件硬列路径。

## 实现位置

- **入口**: `plugins/tools/cortex/scripts/lint.sh` (≤ 80 行 shell, 仅参数解析 + 转发到 python)
- **主体**: `plugins/tools/cortex/scripts/_lint/runner.py`
  - `rules.py` — 每条规则一个 `check_R<n>(vault) -> list[Violation]`
  - `fixers.py` — `fix_R2(v) / fix_R4(v)` 落盘修复
  - `__init__.py` — 数据类 `Violation(file, line, rule, level, msg)`

## 数据流

```
lint.sh
  └─ python -m _lint.runner --target <dir> [--check|--fix] [--rules R1,...]
        ├─ rules.check_R*(vault) → List[Violation]
        ├─ aggregate by rule/level
        ├─ if --fix: fixers.fix_R*(v) for v in violations where autofix
        └─ print summary (stdout) + details (stderr) + exit code
```
