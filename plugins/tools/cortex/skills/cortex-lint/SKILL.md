---
name: cortex-lint
description: lint / 校验 / 体检 / audit / 死链 / 孤儿 / 规范化 / frontmatter — cortex 知识库与记忆树的合规检查与可逆 autofix。检测 wikilink 死链、frontmatter 缺字段、命名违规、目录同构、孤儿页、等级语义反写、脚本目录用途混淆等 7 类规则。
when_to_use:
  - 用户说 "lint" / "体检" / "校验 vault" / "audit"
  - 整理 ~/.cortex/.wiki/ 或 <repo>/.wiki/ 时先跑一遍
  - 排查 wikilink 死链 / 孤儿页
  - frontmatter 字段缺失批量补齐 (按路径推断)
  - 检查 memory/ 子目录是否齐全 (5 级 L0-L4)
  - 检查 memory 路径名与 level 字段一致 (R6 防反写)
  - 项目误建 <repo>/.cortex/scripts/ 用户入口目录 (R7)
  - extract 跑之前先 lint 确保 vault 形态正常
argument-hint: "[--check|--fix] [target]"
---

# cortex-lint

cortex vault 的 7 类合规检查与可逆 autofix。**默认 dry-run** (`--check`), `--fix` 才落盘。

## 入口

```bash
plugins/tools/cortex/scripts/lint.sh [--check|--fix] [--rules R1,R2,...] [--target <dir>]
```

- 默认 `--check` + 全规则
- `--target` 默认 `$HOME/.cortex`
- 退出: 0=无 error; 非 0=有 error (`--check`) 或 fix 失败 (`--fix`)

## 7 类规则

| ID | 规则 | 级别 | autofix? |
| --- | --- | --- | --- |
| R1 | wikilink 解析: `[[X]]` 必须对应 vault 内 .md 文件名或 aliases | warn | 否 (死链不能猜) |
| R2 | frontmatter 必备字段: type 必填; domain→area; rule/memory→level; project→source | error | 是 (按路径推断) |
| R3 | 命名: 领域/ ≥ 2 级; 脚本/ 文件名 kebab-case | warn | 否 (重命名不可逆, 仅提示) |
| R4 | 同构: vault 必备目录齐全 (memory/L0-core ... L4-inbox + 项目 + 领域 + 脚本) | error | 是 (mkdir) |
| R5 | 孤儿: 无反向 wikilink + mtime > 30d 的 .md | warn | 否 (用户审批) |
| R6 | 等级语义一致: 路径后缀 (`core/long/mid/short/inbox`) 严格匹配 level 字段; 反写 (`L1-short`/`L3-long`) 直接 error | error | 否 (用户决定移动哪边) |
| R7 | 脚本目录用途分离: 项目级 `<target>/.cortex/scripts/` 报错; vault 内部 `<root>/.wiki/脚本/` 中文件 frontmatter `type` 应为 `vault-script` 或缺省; 路径写成英文 `<root>/.wiki/scripts/` 视为错位 | warn | 否 |

**级别语义**:
- `error` (R2/R4/R6): `--check` 命中即退出非零, 可机器修复
- `warn` (R1/R3/R5/R7): 仅打印, 不计入退出码, 用户审批后手动改

## R2 frontmatter 推断规则 (fixer 实现)

| 缺失字段 | 推断来源 |
| --- | --- |
| `type` | 路径前缀: `memory/L0-core/` → `rule`; `memory/L1-L4*/` → `memory`; `项目/` → `project`; `领域/` → `domain`; `脚本/` → `vault-script` |
| `area` (domain) | `领域/<area>/...` 路径第 2 段 |
| `level` (rule/memory) | `memory/L([0-4])-` 路径第 3 段中提取 |
| `created` | 文件 mtime (ISO date) |
| `source` (project) | 留空占位 `TODO: fill source URL` (用户必须手填) |

## R6 路径↔level 映射 (权威)

| 路径段 | level 必须 |
| --- | --- |
| `memory/L0-core/` | `L0` |
| `memory/L1-long/` | `L1` |
| `memory/L2-mid/` | `L2` |
| `memory/L3-short/` | `L3` |
| `memory/L4-inbox/` | `L4` |

任何其它形如 `memory/L*-*/` (如 `L1-short` / `L3-long`) 都视为反写 error。

## 输出格式

```
violations: <total>
  error: <e>
  warn:  <w>
by-rule:
  R1: <n>
  R2: <n>
  ...
```

每条详情写 stderr: `<file>:<line?>:<rule>:<msg>`

## 实现

- 入口: `plugins/tools/cortex/scripts/lint.sh` (≤ 80 行 shell, 仅参数解析 + 转发)
- 主体: `plugins/tools/cortex/scripts/_lint/runner.py`
  - `rules.py` — 每条规则一个 `check_R<n>(vault) -> list[Violation]`
  - `fixers.py` — `fix_R2(v) / fix_R4(v)` 落盘
  - `__init__.py` — 数据类 `Violation(file, line, rule, level, msg)`

## fixture

`plugins/tools/cortex/tests/fixtures/lint/` 内置 ≥ 3 类违规:

- 死 wikilink: `领域/tech/sub/foo.md` 含 `[[不存在的页]]` (R1 warn)
- 缺 area: `领域/life/bar.md` `type: domain` 但无 `area` (R2 error)
- 命名违规: `脚本/BadCamelCase.sh` (R3 warn)
- 路径反写: `memory/L1-short/test.md` (R6 error)
- 目录缺项: 缺 `memory/L0-core/` (R4 error)

## 验收

```bash
# Skill frontmatter
python3 -c "import yaml; fm=yaml.safe_load(open('plugins/tools/cortex/skills/cortex-lint/SKILL.md').read().split('---')[1]); assert fm['name']=='cortex-lint' and fm['description']; print('OK')"

# Check 必报多违规
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ ; [[ $? -ne 0 ]] && echo CHECK-FAIL-AS-EXPECTED

# Fix
bash plugins/tools/cortex/scripts/lint.sh --fix --target plugins/tools/cortex/tests/fixtures/lint/

# 再 check: error 应全部消失 (warn 还在)
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/
```

## 引用

- 目录契约: `plugins/tools/cortex/docs/layout.md`
- 三模块 schema: `cortex-schema-knowledge`
- 记忆等级 schema: `cortex-schema-memory`
- extract (lint 通过后跑): `cortex-extract`
