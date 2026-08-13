# lint fixture

cortex-lint 测试 fixture, 故意包含若干违规:

| 违规 | 文件 | 规则 | 级别 | 可 fix? |
| --- | --- | --- | --- | --- |
| dead wikilink | `domains/tech/sub/foo.md` 含未定义 wiki 链接 | R1 | warn | 否 |
| missing area | `domains/life/bar.md` (type=domain 无 area) | R2 | error | 是 |
| missing type+level | `memory/L2-mid/note.md` (memory 路径无 frontmatter type) | R2 | error | 是 |
| naming | `scripts/BadCamelCase.sh` | R3 | warn | 否 |
| domain shallow | `domains/life/bar.md` 仅 1 级 | R3 | warn | 否 |
| missing L0-core | `memory/L0-core/` 不存在 | R4 | error | 是 (mkdir) |

## 使用

```bash
# 初始 check (预期 rc=1, 3 error + 3 warn)
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/

# 落盘 fix
bash plugins/tools/cortex/scripts/lint.sh --fix --target plugins/tools/cortex/tests/fixtures/lint/

# fix 后 check (预期 rc=0, 仅 3 warn)
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/
```

## 重置 fixture

`--fix` 会写入 frontmatter + mkdir L0-core. 重置:

```bash
git checkout plugins/tools/cortex/tests/fixtures/lint/
git clean -fd plugins/tools/cortex/tests/fixtures/lint/
```
