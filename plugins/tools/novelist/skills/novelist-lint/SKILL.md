---
name: novelist-lint
description: '校验 novelist 插件目录结构/文件名/文件夹组织是否符合插件规范 (plugin.json 合法 / commands-agents-skills 在根 / SKILL.md 大写 / kebab 命名 / 无产物泄漏 / plugin.json 路径真实 / frontmatter name 对齐)。novelist 插件改动后、加新 skill/agent 后、发布前、或怀疑结构不合规时调用。调用即跑 scripts/lint.py 扫 7 规则违规, 按 fix-hints 移/改/删到合规'
when_to_use: 'novelist 插件结构校验: 加新 skill/agent 后、改 plugin.json 后、发布前、发现可疑文件/命名时。禁用于非 novelist 插件 (本 skill 专属, 但 lint.py 可对任意插件目录跑)'
---

# novelist-lint — 插件目录结构校验

校验 `plugins/tools/novelist/` 目录结构、文件名、文件夹组织是否符合 `docs/plugin-development.md` 规范。不合规的按修复指引移动/重命名/删除。

## 何时触发

- novelist 加了新 skill / agent 后，校验命名 + 结构
- 改动 plugin.json 后，校验路径字段真实存在
- 发布前完整校验
- 发现可疑文件（如 `.DS_Store`、测试产物、缓存目录）泄漏进插件目录

## 7 规则速查

| 规则 | 检查 | 严重级 |
|---|---|---|
| R1 | `.claude-plugin/plugin.json` 存在 + 合法 JSON + `name` 匹配 `^[a-z0-9-]+$` | error |
| R2 | `commands/`/`agents/`/`skills/` 在插件根，不在 `.claude-plugin/` 内 | error |
| R3 | `skills/*/` 目录名 kebab-case + 含大写 `SKILL.md` | error |
| R4 | `agents/*.md` 文件名 kebab-case | error |
| R5 | 无产物泄漏 (`.DS_Store`/`__pycache__`/`*.pyc`/`.darwin-results.tsv`/`*.bak`) | warning |
| R6 | plugin.json 中 `agents`/`skills`/`commands`/`hooks` 路径真实存在 | error |
| R7 | skill SKILL.md frontmatter `name` == 目录名 | warning |

规则定义 + 违规/合规示例 + 修复命令见 `references/lint-rules.md`。

## 调用方式

```bash
# 校验 novelist 插件 (默认上溯找 .claude-plugin/ 定位插件根)
python3 plugins/tools/novelist/skills/novelist-lint/scripts/lint.py --plugin-dir plugins/tools/novelist --fix-hints

# 也可对任意插件目录跑
python3 <lint.py 路径> --plugin-dir <插件根>
```

**输出**:
- 每规则 PASS / ERROR / WARNING
- 违规项列出文件路径 + message + (可选) fix hint
- exit code: `0` 全 PASS / `1` 有 error / `2` 仅 warning / `3` 找不到插件根

## 修复流程

1. 跑 `lint.py --fix-hints` 看违规清单
2. 按 fix hint 逐项修:
   - **R5 产物泄漏**: `rm <file>` 或加 `.gitignore`
   - **R3/R4 命名违规**: `git mv` 改名 (注意同步 plugin.json 引用)
   - **R2 目录位置**: `mv .claude-plugin/<sub> ./<sub>`
   - **R6 路径不存在**: 改 plugin.json 或 `git mv` 文件对齐
   - **R7 frontmatter**: 改 SKILL.md frontmatter `name`
3. 重跑 lint 直到全 PASS

## 边界

- **仅校验目录结构/命名/产物**, 不校验内容质量 (SKILL.md 写得好不好归人工 review)
- **不替代** `scripts/check.py` (后者覆盖 plugin.json 格式/hook 测试/name alignment, 但有 skills.bak bug; 两者并用)
- **只读校验**, `--fix-hints` 只打印建议不自动执行 (避免误删)
- lint.py 可对任意插件目录跑, 但本 SKILL.md 的触发语境限定 novelist

## 与 check.py 的分工

| 维度 | novelist-lint | scripts/check.py |
|---|---|---|
| plugin.json 格式 | R1 (name 合规) | ✓ (全字段) |
| 目录结构 | R2/R3/R4 (skills 目录名/SKILL.md/agent 命名) | 有 bug (检查 skills.bak 非 skills) |
| 产物泄漏 | R5 (独有) | ✗ |
| 路径存在 | R6 | 部分 |
| frontmatter 对齐 | R7 (独有) | ✗ |
| hooks 测试 | ✗ | ✓ |
| name alignment (跨 marketplace) | ✗ | ✓ |

两者并用: check.py 查配置/hook/marketplace 对齐, 本 lint 查结构/命名/产物。
