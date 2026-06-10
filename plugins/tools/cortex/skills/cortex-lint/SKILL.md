---
name: cortex-lint
description: lint / 校验 / 体检 / audit / 死链 / 孤儿 / 规范化 / frontmatter — cortex 知识库与记忆树的合规检查与可逆 autofix。覆盖 wikilink 死链、frontmatter 缺字段、命名违规、目录同构、孤儿页、等级语义反写、脚本目录用途混淆等 7 类规则。默认 dry-run (--check)，--fix 才落盘。
when_to_use: "lint/体检/校验 vault/audit; 整理 .wiki/ 前先跑; 排查死链/孤儿; frontmatter 补齐; memory 5 级目录核对; extract 前的形态检查"
argument-hint: "[--check|--fix] [target]"
arguments: "[--check|--fix] [路径]"
user-invocable: true
disable-model-invocation: true
---

# cortex-lint

cortex vault 的 7 类合规检查与可逆 autofix。默认 dry-run (`--check`)，`--fix` 才落盘。

## 入口

```bash
plugins/tools/cortex/scripts/lint.sh [--check|--fix] [--rules R1,R2,...] [--target <dir>]
```

默认 `--check` + 全规则；`--target` 默认 `$HOME/.cortex`；退出 0=无 error，非 0=有 error 或 fix 失败。

## 7 规则速查

| ID | 规则 | 级别 | autofix |
| --- | --- | --- | --- |
| R1 | wikilink 死链 | warn | 否 |
| R2 | frontmatter 必备字段 | error | 是 (按路径推断) |
| R3 | 命名 (领域 ≥2 级, 脚本 kebab) | warn | 否 |
| R4 | 同构 (memory L0-L4 + 三模块齐全) | error | 是 (mkdir) |
| R5 | 孤儿页 (无反链 + mtime>30d) | warn | 否 |
| R6 | 等级语义一致 (路径↔level) | error | 否 |
| R7 | 脚本目录用途分离 | warn | 否 |

`error` 命中即非零退出且机器可修；`warn` 仅打印。

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 7 规则具体定义 / 检测策略 | `references/rules.md` |
| 查 R2 推断 / R4 mkdir / lint.sh + _lint/ 实现 | `references/fixers.md` |
| 查 stdout/stderr 格式 + fixture + 验证命令 | `references/output.md` |

## 引用

- 目录契约权威: `cortex-schema` (顶层 + 三模块 + 5 级)
- 三模块 schema: `cortex-schema`
- 记忆等级 schema: `cortex-schema`
- extract (lint 通过后跑): `cortex-extract`
