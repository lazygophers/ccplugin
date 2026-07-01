# Design — novelist-lint skill

## 边界

lint skill = novelist 专属。校验对象 = 单个插件目录 (`plugins/tools/novelist/` 或 `--plugin-dir` 指定)。不校验跨插件 marketplace。

## lint.py 架构

### 数据模型

```python
@dataclass
class Violation:
    rule: str          # "R1".."R7"
    severity: str      # "error" | "warning"
    path: str          # 相对插件根的路径
    message: str       # 违规描述 + 修复指引

@dataclass
class LintReport:
    plugin_dir: Path
    violations: list[Violation]
    @property
    def has_errors(self) -> bool: ...   # 任一 error 级
```

### 规则实现 (7 条, 每条一个函数)

| 函数 | 规则 | 逻辑 |
|---|---|---|
| `check_r1_plugin_json` | R1 | `.claude-plugin/plugin.json` 存在 + 合法 JSON + `name` 字段匹配 `^[a-z0-9-]+$` |
| `check_r2_root_dirs` | R2 | `commands/`/`agents/`/`skills/` 若存在必须在根, 不在 `.claude-plugin/` 内 (扫 `.claude-plugin/` 下有无这些子目录) |
| `check_r3_skill_dirs` | R3 | 遍历 `skills/*/`, 子目录名匹配 `^[a-z0-9-]+$` + 含文件 `SKILL.md` (大写, 不是 skill.md) |
| `check_r4_agent_files` | R4 | 遍历 `agents/*.md`, 文件名 stem 匹配 `^[a-z0-9-]+$` |
| `check_r5_artifacts` | R5 | 扫全树, 命中产物 pattern (`.DS_Store`/`__pycache__`/`*.pyc`/`.darwin-results.tsv`/`*.bak` 目录) |
| `check_r6_plugin_json_paths` | R6 | 读 plugin.json 的 `agents`/`skills`/`commands` 字段, 指向路径真实存在 |
| `check_r7_skill_frontmatter` | R7 | 每个 skill SKILL.md frontmatter `name` 字段 == 目录名 |

### CLI

```bash
python3 lint.py [--plugin-dir <path>] [--fix-hints]
# 默认 --plugin-dir = 脚本所在插件的根 (上溯找 .claude-plugin/)
# --fix-hints: 每条违规附修复建议 (mv/rm 命令模板)
# 输出: 人类可读 (rich table) + exit code (0=全 pass, 1=有 error, 2=仅 warning)
```

### 输出格式

```
novelist lint report
─────────────────────
✓ R1 plugin.json         PASS  name=novelist 合法
✗ R5 artifacts           WARN  skills/.darwin-results.tsv (测试产物泄漏)
  fix: rm skills/.darwin-results.tsv
✓ R3 skill dirs          PASS  13/13 skill 目录合规
...

Summary: 1 warning, 0 errors → exit 2
```

## SKILL.md 设计

frontmatter:
```yaml
---
name: novelist-lint
description: '校验 novelist 插件目录结构/文件名/文件夹组织是否符合插件规范 (plugin.json/根目录位置/SKILL.md 大写/kebab 命名/无产物泄漏)。novelist 插件改动后、发布前、或怀疑结构不合规时调用。调用即跑 lint.py 扫违规, 按 fix-hints 移/改/删到合规'
when_to_use: 'novelist 插件改动后校验结构合规, 或发现可疑文件/命名时。禁用于非 novelist 插件 (本 skill 专属)'
---
```

body: 7 规则速查表 + 调用方式 (`python3 scripts/lint.py --plugin-dir .`) + 常见违规修复手册 + 与 check.py 关系说明 (独立, 不替代)。

## 兼容性

- lint.py 纯 stdlib (pathlib/json/re/dataclasses/argparse), 无外部依赖
- Python 3.9+ (novelist 其他脚本同要求)
- 不写盘 (只读校验), `--fix-hints` 只打印建议不自动执行 (避免误删)

## 失败处理

- plugin.json 解析失败 → R1 error, 跳过 R6 (依赖 plugin.json)
- 路径不存在 → 各规则独立报错, 不中断
- lint.py 自身异常 → exit 3 + traceback
