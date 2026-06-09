# Fixer 实现 (R2 / R4) + 代码位置

## R2 frontmatter 推断规则

| 缺失字段 | 推断来源 |
| --- | --- |
| `type` | 路径前缀: `memory/L0-core/` → `rule`; `memory/L1-L4*/` → `memory`; `项目/` → `project`; `领域/` → `domain`; `脚本/` → `vault-script` |
| `area` (domain) | `领域/<area>/...` 路径第 2 段 |
| `level` (rule/memory) | `memory/L([0-4])-` 路径第 3 段中提取 |
| `created` | 文件 mtime (ISO date) |
| `source` (project) | 留空占位 `TODO: fill source URL` (用户必须手填) |

写回策略: 保留原 frontmatter 顺序与注释，仅在末尾追加缺失字段；如原文件无 frontmatter，则在文件最顶补一段 `---\n...\n---\n`。

## R4 mkdir 修复

对缺失目录直接 `os.makedirs(path, exist_ok=True)`，不写占位文件。

待补清单 (绝对覆盖):

```
<target>/.wiki/memory/L0-core/
<target>/.wiki/memory/L1-long/
<target>/.wiki/memory/L2-mid/
<target>/.wiki/memory/L3-short/
<target>/.wiki/memory/L4-inbox/
<target>/.wiki/项目/
<target>/.wiki/领域/
<target>/.wiki/脚本/
```

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
