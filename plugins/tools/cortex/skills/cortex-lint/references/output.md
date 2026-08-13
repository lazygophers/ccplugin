# 输出格式 + fixture + 验证

## stdout (摘要)

```
violations: <total>
  error: <e>
  warn:  <w>
by-rule:
  R1: <n>
  R2: <n>
  R3: <n>
  R4: <n>
  R5: <n>
  R6: <n>
  R7: <n>
```

## stderr (详情)

每行一条违规:

```
<file>:<line?>:<rule>:<msg>
```

- `<file>` 相对 vault 根
- `<line>` 仅 R1/R2 有意义 (wikilink 行号 / frontmatter 字段行号), 其它留空
- `<rule>` R1..R7
- `<msg>` 简短机器友好原因, 如 `missing field: area` / `dead wikilink: 不存在的页` / `path-level mismatch: L1-short`

## 退出码

- `--check`: 0 = 无 error; 非 0 = 有 error (warn 不计)
- `--fix`: 0 = 全部 error 已修 / 无 error; 非 0 = fix 失败 (磁盘错 / 推断失败)

## fixture

`plugins/tools/cortex/tests/fixtures/lint/` 内置 ≥ 3 类违规:

- 死 wikilink: `领域/tech/sub/foo.md` 含 `[[不存在的页]]` (R1 warn)
- 缺 area: `领域/life/bar.md` `type: domain` 但无 `area` (R2 error)
- 命名违规: `脚本/BadCamelCase.sh` (R3 warn)
- 路径反写: `memory/L1-short/test.md` (R6 error)
- 目录缺项: 缺 `memory/L0-core/` (R4 error)

## 验证命令

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
