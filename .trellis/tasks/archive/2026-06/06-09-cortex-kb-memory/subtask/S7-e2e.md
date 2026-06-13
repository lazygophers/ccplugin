---
id: S7
slug: e2e
deliverable: all
parent-task: 06-09-cortex-kb-memory
status: planned
execution-layer: main
isolation: none
depends-on: [S6]
blocks: []
estimated-tokens: 5000
---

# S7 · 端到端 fixture 验收

## 目标

跑 validate-layout + lint + extract 全链路 + AI 识别测试, 确认 6 个 deliverable 协作无回归, PRD 验收清单全打钩。

## 产出

- `plugins/tools/cortex/tests/fixtures/e2e/` (完整模拟 ~/.cortex/.wiki/ 结构 + L4-inbox 样本)
- `plugins/tools/cortex/tests/e2e-report.md` (本次跑链路的报告: 命令 / 退出码 / 关键 stdout 摘要)
- PRD 验收清单逐项打钩

## 验证

```bash
# 链路 1: 布局
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/e2e/

# 链路 2: lint --check → fix → check
bash plugins/tools/cortex/scripts/lint.sh --check plugins/tools/cortex/tests/fixtures/e2e/ || true
bash plugins/tools/cortex/scripts/lint.sh --fix plugins/tools/cortex/tests/fixtures/e2e/
bash plugins/tools/cortex/scripts/lint.sh --check plugins/tools/cortex/tests/fixtures/e2e/   # 必须 0

# 链路 3: extract dry-run → apply
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/e2e/
bash plugins/tools/cortex/scripts/extract.sh --apply --target plugins/tools/cortex/tests/fixtures/e2e/

# 链路 4: 再跑布局确认结构未坏
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/e2e/

# 链路 5: AI 识别测试 (项目 CLAUDE.md 要求)
for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
  result=$(claude \
    -p "$(cat plugins/tools/cortex/skills/$s/SKILL.md)" \
    --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result')
  [[ -n "$result" ]] && echo "OK: $s" || echo "FAIL: $s"
done
```

期望: 全部退出 0; 5 行 "OK: <skill>"。

## 资源

- 只读: 全部脚本与 skill
- 写: `plugins/tools/cortex/tests/fixtures/e2e/**` `plugins/tools/cortex/tests/e2e-report.md`
- 审批槽位: 否 (G1 已在 S6 后过)

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S6 | plugin.json + agent + 4 skill 注册完成 | 验证 S6 命令通过 |

## 执行细节

1. 建 fixture `tests/fixtures/e2e/`, 结构镜像 `~/.cortex/.wiki/`:
   - `.wiki/memory/L0-core/example-rule.md`
   - `.wiki/memory/L1-long/` (空, 长期记忆)
   - `.wiki/memory/L2-mid/` (空, 中期记忆)
   - `.wiki/memory/L3-short/` (空, 短期记忆 — extract 默认入口)
   - `.wiki/memory/L4-inbox/sample-1.md` 到 `sample-5.md` (5 类样本)
   - `.wiki/projects/github.com/lazygophers/ccplugin/README.md`
   - `.wiki/domains/tech/cortex/design.md`
   - `.wiki/scripts/.gitkeep` (vault 内部脚本目录)
   - 顶层 `config/`, `state/`, `scripts/` (用户操作入口), `logs/`
2. 按"验证"节顺序跑命令, 收集每条退出码 + 关键 stdout (前 5 行)
3. 写 `e2e-report.md`: 每个命令 / 退出码 / 摘要 / OK or FAIL
4. 把 PRD 验收清单 7 条逐条打钩 (或标 FAIL 并说明)
5. 任一 FAIL → 标记 task blocked, 回对应 phase 修

## 回滚

- 触发条件: fixture 本身写错导致全链失败
- 步骤:
  ```bash
  rm -rf plugins/tools/cortex/tests/fixtures/e2e/ plugins/tools/cortex/tests/e2e-report.md
  ```
  注: 不回滚 S1-S6 产出, 它们已通过各自验收

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| `claude --settings glm-4.7-flash.json` 命令在 CI / 当前环境不可用 | 链路 5 跑不了 | 文档标"本地手动跑"; 不强求 CI 自动化 |
| extract --apply 修改 fixture 后导致 lint 重跑失败 | 链路 2/3 顺序敏感 | 链路顺序固定: layout → lint → extract → layout (lint 在 extract 前) |
| AI 识别返回空但 skill 实际 OK | 链路 5 假阴 | 留 `--retry 2` 或人工复核选项 |

## 历史

- 2026-06-09: created
