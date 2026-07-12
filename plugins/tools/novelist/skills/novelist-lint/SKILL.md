---
name: novelist-lint
description: '校验 novelist 插件目录结构/文件名/文件夹组织是否符合插件规范 (plugin.json 合法 / commands-agents-skills 在根 / SKILL.md 大写 / kebab 命名 / 无产物泄漏 / plugin.json 路径真实 / frontmatter name 对齐)。novelist 插件改动后、加新 skill/agent 后、发布前、或怀疑结构不合规时调用。调用即跑 scripts/lint.py 扫 7 规则违规, 按 fix-hints 移/改/删到合规'

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
2. 🔴 **CHECKPOINT (破坏性修复前必停)**: R5 的 `rm` 与 R3/R4/R2/R6 的 `git mv`/`mv` 会删/移文件, **执行前先把该项 (文件路径 + 动作) 报用户确认, 得到明确同意再动手**。只读改文本内容的 R7 无需停。
3. 按 fix hint 逐项修:
   - **R5 产物泄漏**: `rm <file>` 或加 `.gitignore`
   - **R3/R4 命名违规**: `git mv` 改名 (注意同步 plugin.json 引用)
   - **R2 目录位置**: `mv .claude-plugin/<sub> ./<sub>`
   - **R6 路径不存在**: 改 plugin.json 或 `git mv` 文件对齐
   - **R7 frontmatter**: 改 SKILL.md frontmatter `name`
4. 重跑 lint 直到全 PASS

## 失败处理 (触发条件 → 一线修复 → 仍失败兜底)

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| exit 3 找不到插件根 | 确认 `--plugin-dir` 指向含 `.claude-plugin/` 的目录 | 手动定位 `.claude-plugin/plugin.json` 所在层作为插件根传入 |
| lint.py 报 `JSONDecodeError` (R1) | plugin.json 语法坏 → `python3 -m json.tool plugin.json` 定位坏行修复 | 从 git 历史 `git show HEAD:<path>` 取上一版对照重写 |
| `git mv` 改名后 lint 仍报 R6 | plugin.json 仍引用旧路径 → 同步改 plugin.json 对应字段 | 全局 `grep -rn '<旧文件名>' plugins/tools/novelist` 找残留引用逐个改 |
| R7 改 name 后 check.py 仍报 name 不齐 | check.py 查的是 marketplace 层对齐, 非本 skill 范围 → 转 check.py 修复流程 | 两工具并用, 以 check.py 的 marketplace 校验为准 |
| lint.py 自身崩溃 (非违规报错) | 确认 python3 可用 + lint.py 未被改坏 | `git checkout plugins/tools/novelist/skills/novelist-lint/scripts/lint.py` 复原脚本 |

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

## 反例黑名单 (命中即错)

| ✗ 不要 | 为什么 | ✓ 替代 |
|---|---|---|
| 见 R5 违规直接 `rm -rf` | `--fix-hints` 只打印建议; 误删无法回滚 | 先报用户确认单个文件再 `rm`, 优先加 `.gitignore` |
| `git mv` 改名后不同步 plugin.json | R6 立刻挂, 且运行时插件加载失败 | 改名与 plugin.json 引用同一步双写 |
| 把 lint.py 当内容质量审查 | 只校验结构/命名/产物, 不看 SKILL.md 写得好不好 | 内容质量走人工 review / darwin-skill |
| 因 check.py 报错就改 lint 的 R 规则 | 两工具范围不同 (check 管 marketplace/hook) | 按各自分工表定位到对的工具 |
| 对非 novelist 插件默认套用本 SKILL 语境 | 触发语境限定 novelist (lint.py 本身可跑任意插件) | 跑任意插件只用 lint.py CLI, 不套本 skill 修复流程 |
| exit 3 时瞎猜插件根路径反复试 | 浪费轮次且可能改错目录 | 直接定位 `.claude-plugin/plugin.json` 所在层 |
