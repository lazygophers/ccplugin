# Implement — novelist-lint skill 执行清单

## D1: lint.py

新建 `plugins/tools/novelist/skills/novelist-lint/scripts/lint.py`:

- [ ] `Violation` / `LintReport` dataclass
- [ ] 7 个 `check_rN` 函数 (按 design.md 表)
- [ ] `main()`: argparse (`--plugin-dir` 默认上溯找 `.claude-plugin/`, `--fix-hints`), 跑全部规则, rich table 输出, exit code (0/1/2/3)
- [ ] 产物 pattern: `.DS_Store`, `__pycache__`, `*.pyc`, `.darwin-results.tsv`, `*.bak` 目录
- [ ] kebab 正则: `^[a-z0-9-]+$`
- [ ] name 正则: 同上 (plugin.json name + skill 目录名 + agent 文件名)
- [ ] SKILL.md 大写精确匹配 (`SKILL.md`, 不是 `skill.md`/`Skill.md`)

验证:
```bash
cd plugins/tools/novelist/skills/novelist-lint && python3 scripts/lint.py --plugin-dir ../..
# 预期: R5 报 skills/.darwin-results.tsv warning, 其余 pass
```

## D2: lint-rules.md

新建 `references/lint-rules.md`:
- [ ] 7 规则逐条: 定义 + 违规示例 + 合规示例 + 修复命令
- [ ] 与 check.py 关系说明 (独立工具, check.py 有 skills.bak bug 不覆盖)

## D3: SKILL.md

新建 `SKILL.md`:
- [ ] frontmatter (name/description/when_to_use, description 前置触发词)
- [ ] 7 规则速查表
- [ ] 调用方式 (`python3 scripts/lint.py --plugin-dir <novelist根>`)
- [ ] 常见违规修复手册 (产物删除 / 命名改 / 路径修)
- [ ] 边界: 仅 novelist, 不替代 check.py

## D4: 应用修复

- [ ] 删 `plugins/tools/novelist/skills/.darwin-results.tsv`
- [ ] 查 `.gitignore` 是否已覆盖 `.darwin-results.tsv`, 无则加 (path-scoped, 不污染)
- [ ] 重跑 lint, 全 PASS (0 error, 0 warning)

## D5: 质检

```bash
# A. lint.py 对 novelist 跑, exit code 0 + 全 PASS
python3 plugins/tools/novelist/skills/novelist-lint/scripts/lint.py --plugin-dir plugins/tools/novelist

# B. claude -p 验 SKILL.md 触发识别
claude -p "读 plugins/tools/novelist/skills/novelist-lint/SKILL.md。novelist 加了个新 skill 但不确定目录结构对不对, 该怎么做? 引用 SKILL 原文。" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'

# C. lint.py 自检: 故意建个违规 (tmp 目录) 验能检出, 再删 tmp
```

## 验证命令汇总

- D4 lint exit 0
- D5-B claude -p 返回"跑 lint.py 校验"语义
- D5-C 故意违规能检出 (R3/R4/R5 各验一个)

## Rollback

- lint.py/SKILL.md/lint-rules.md 新文件 → `git checkout` 不影响 (未追踪删即可)
- .darwin-results.tsv 删除 → `git checkout -- <file>` 恢复 (已追踪)
- .gitignore 改动 → `git checkout -- .gitignore`
