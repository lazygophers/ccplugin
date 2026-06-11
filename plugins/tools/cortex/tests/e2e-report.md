# E2E 验收报告 — cortex-kb-memory

任务: 06-09-cortex-kb-memory
日期: 2026-06-09
fixture: `plugins/tools/cortex/tests/fixtures/e2e/`

## 链路结果

| Step | 命令 | rc | 结论 |
| --- | --- | --- | --- |
| 1 | `validate-layout.sh --target e2e/` | 0 | OK: 14 required paths present |
| 2 | `lint.sh --check --target e2e/` | 1 | 检出 4 R2 error (L4-inbox 5 文件缺 type/level, 1 已有 type 不计) |
| 3 | `lint.sh --fix --target e2e/` | 0 | fixed: 4; 0 残留 |
| 4 | `lint.sh --check --target e2e/` (复查) | 0 | violations: 0 |
| 5 | `extract.sh --dry-run --target e2e/` | 0 | plan-len=5, 路由正确: L3 / L0 / 项目 / 领域 / L3 (--dry-run opt-in 预览) |
| 6 | `extract.sh --apply --target e2e/` | 0 | 5 全落盘 (含 L0-core 默认自动写, 不再 ask) |
| 7 | `validate-layout.sh --target e2e/` (复查) | 0 | 结构未坏 |
| 8 | cursor 状态 | OK | `state/extract-cursor.json` 含 4 sha256 |

## 路由实况

| 源文件 | 目标 | 决策 |
| --- | --- | --- |
| `L4-inbox/01-临时.md` | `memory/L3-short/01-临时.md` | "暂时" 关键词 → L3 (默认入口) |
| `L4-inbox/02-永久.md` | `memory/L0-core/02-永久.md` | weight=0.9 + "永远" → L0-core, 默认自动落盘 |
| `L4-inbox/03-项目-tokio.md` | `项目/github.com/tokio-rs/tokio/README.md` | URL 命中 |
| `L4-inbox/04-领域-go.md` | `领域/tech/general/04-领域-go.md` | type=domain + area=tech |
| `L4-inbox/05-复用.md` | `memory/L3-short/05-复用.md` | "暂时" → L3 |

archive: 5 个 inbox 文件移到 `L4-inbox/_archived/`, 原位删除.

## PRD 验收清单逐项

- [x] D1-D6 全部 P0 deliverable 通过各自独立验收 — 见 Step 1-7
- [x] `plugin.json` JSON 校验通过, skills=4, agents=1
- [x] 4 SKILL.md frontmatter 含非空 name/description/when_to_use
- [x] `validate-layout.sh` 对 fixture 通过 (layout-ok rc=0, layout-bad rc=1)
- [x] `lint.sh --check tests/fixtures/lint/` 检出预期违规, `--fix` 后再 `--check` rc=0
- [x] `extract.sh --dry-run tests/fixtures/extract/` 产出预期归档计划
- [x] cortex agent 边界条款明确 (只读 .trellis/, 写仅限 ~/.cortex/ 与 <repo>/.wiki/)
- [ ] **N/A** — `claude --settings ~/.claude/settings.glm-4.7-flash.json` AI 识别测试: 本机无 glm-4.7-flash settings 文件, 此项跳过. 后续 task 可单独跑.

## 反直觉防呆验证

| 检查 | 结果 |
| --- | --- |
| 落盘后无 `L1-short/L1-recent/L3-long` 等反写路径 | OK (find 无匹配) |
| level=L3 仅出现在 `memory/L3-short/` | OK |
| extract 默认入口 = L3-short (新条目不进 L1) | OK (Step 5 plan 显示) |
| L0 候选默认自动落盘 (--apply 直接写, 不再 ask) | OK (Step 6 验证, 02-永久.md 落 L0-core) |

## 三模块中文化验证 (G1.1)

| 检查 | 结果 |
| --- | --- |
| `~/.cortex/.wiki/项目 领域 脚本` 中文目录名 | OK (fixture + extract 输出) |
| `~/.cortex/scripts/` 英文 (用户操作入口) | OK (validate-layout 校验) |
| 三模块内部子目录英文 (kebab-case) | OK (`项目/github.com/lazygophers/ccplugin/`) |

## 抗遗忘度阈值验证 (G1.2)

- L1=365d / L2=90d / L3=7d 阈值写入 `cortex-schema/references/memory-levels.md`
- 当前实现仅 lint/extract 路由用语义, 阈值真正生效的 demote 由后续 task 实现 (本 task 范围内仅契约)

## 已知限制

- AI 识别测试 (`claude --settings`) 需本机有对应 settings 文件, 不阻塞本 task
- L0-core 写入默认自动落盘 (不再 ask), 与其他级别一致
- demote 自动迁移 (L1→L2→L3→forget 标记) 当前只写在契约, 未实现 cron / hook
