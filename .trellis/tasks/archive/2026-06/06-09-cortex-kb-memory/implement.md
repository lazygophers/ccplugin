# Implement — cortex plugin: knowledge base + memory management system

## 执行有序 checklist

按调度图执行 (S1 → S2//S3 → S4//S5 → S6 → G1 → S7)。每步标 `[L?]` = 执行层 (L1=main, L2=skill main, L3=sub-agent)。

### Phase A — 目录契约 (S1, 串行基础)

- [ ] **[L1] S1.1** 写 `plugins/tools/cortex/docs/layout.md` (依据 design.md "系统边界" 章节)
- [ ] **[L1] S1.2** 写 `plugins/tools/cortex/scripts/validate-layout.sh`, 实现:
  - 接受 `--target <dir>` 参数
  - 校验 ~/.cortex/ 顶层有 `.wiki/ config/ state/ scripts/ logs/` (其中 `scripts/` = 用户操作入口)
  - 校验 .wiki/ 含 `memory/L0-core memory/L1-long memory/L2-mid memory/L3-short memory/L4-inbox projects/ domains/ scripts/` (其中 `scripts/` = vault 内部脚本)
  - 缺失项输出到 stderr 并 exit 1
- [ ] **[L1] S1.3** 写 fixture: `tests/fixtures/layout-ok/` (合规) + `tests/fixtures/layout-bad/` (缺项)
- [ ] **[L1] S1.4** 验证: `bash scripts/validate-layout.sh --target tests/fixtures/layout-ok/` 退出 0; `--target tests/fixtures/layout-bad/` 退出 ≠ 0
- [ ] **[L1] S1.5** `git add` 暂存

### Phase B — 并行写 schema (S2 // S3)

可派两个 sub-agent 并行 (改不同目录, 资源不互斥):

- [ ] **[L3] S2** dispatch `trellis-implement` 写 `skills/cortex-schema-knowledge/SKILL.md`
  - dispatch prompt 见 `subtask/S2-schema-knowledge.md`
- [ ] **[L3] S3** dispatch `trellis-implement` 写 `skills/cortex-schema-memory/SKILL.md`
  - dispatch prompt 见 `subtask/S3-schema-memory.md`
- [ ] **[L1]** 等两 agent 都返回, 任一失败暂停后续阶段
- [ ] **[L1]** 跑两份 frontmatter YAML 校验, 验证 description 含触发词
- [ ] **[L1]** `git add` 暂存

### Phase C — 并行写脚本 skill (S4 // S5)

依赖 Phase B 输出 (schema 已落). 派两个 sub-agent 并行:

- [ ] **[L3] S4** dispatch `trellis-implement` 写 `skills/cortex-lint/` + `scripts/lint.sh` + `tests/fixtures/lint/`
  - dispatch prompt 见 `subtask/S4-lint.md`
- [ ] **[L3] S5** dispatch `trellis-implement` 写 `skills/cortex-extract/` + `scripts/extract.sh` + `tests/fixtures/extract/`
  - dispatch prompt 见 `subtask/S5-extract.md`
- [ ] **[L1]** 等两 agent 都返回
- [ ] **[L1]** 跑各自 fixture 验证 (见 design.md "验证契约")
- [ ] **[L1]** `git add` 暂存

### Phase D — Agent + plugin.json 收口 (S6, 串行)

- [ ] **[L1] S6.1** 改写 `agents/cortex.md`: 协调 4 skill 的主代理, 边界条款 (只读 .trellis/, 写仅限 ~/.cortex 与 <repo>/.wiki)
- [ ] **[L1] S6.2** 更新 `.claude-plugin/plugin.json`:
  - `skills` 数组 = 4 个 ("./skills/cortex-schema-knowledge", "./skills/cortex-schema-memory", "./skills/cortex-lint", "./skills/cortex-extract")
  - `agents` 数组 = `["./agents/cortex.md"]`
  - `description` 更新为正式描述 (替换占位 TODO)
  - `keywords` 补齐: cortex / knowledge-base / memory / vault / lint / extract
- [ ] **[L1] S6.3** 删除骨架 `skills/cortex/` 目录 (被 4 个具名 skill 取代)
- [ ] **[L1] S6.4** 更新 `README.md` + `llms.txt`: 描述 4 skill + agent + 目录契约
- [ ] **[L1] S6.5** 验证: plugin.json JSON 校验; skill 数 == 4; agent 数 == 1
- [ ] **[L1] S6.6** `git add` 暂存

### Phase E — Review Gate G1

- [ ] **[L1] G1** 用 AskUserQuestion 走 review:
  - Q1: 三模块命名 (projects/domains/scripts) 是否调整?
  - Q2: 抗遗忘度阈值 (L1 长期 365d / L2 中期 90d / L3 短期 7d) 是否合理?
  - Q3: 4 skill 的 description 触发词是否覆盖典型用法?
- [ ] **[L1]** 用户驳回 → 回到 Phase B/C 改对应 skill, 再来 G1
- [ ] **[L1]** 用户通过 → 进 Phase F

### Phase F — E2E 验收 (S7, 串行收口)

- [ ] **[L1] S7.1** 写 `tests/fixtures/e2e/` (完整模拟 ~/.cortex/.wiki/ 一份)
- [ ] **[L1] S7.2** 跑 validate-layout → lint --check → lint --fix → extract --dry-run → extract --apply → validate-layout 完整链
- [ ] **[L1] S7.3** 跑项目 CLAUDE.md 要求的 skill 识别测试:
  ```bash
  for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
    claude --settings ~/.claude/settings.glm-4.7-flash.json \
      -p "$(cat plugins/tools/cortex/skills/$s/SKILL.md)" \
      --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result' | head -5
  done
  ```
  每个 skill 返回非空有意义结果
- [ ] **[L1] S7.4** 跑 PRD 验收清单, 逐项打钩
- [ ] **[L1] S7.5** `git add` 暂存

### Phase G — 收尾

- [ ] **[L1]** trellis-update-spec (如果学到新规则)
- [ ] **[L1]** 用户授权后 commit (按 enable auto commit 协议)
- [ ] **[L1]** `/trellis:finish-work` 归档

## 验证命令汇总

```bash
# 布局
bash plugins/tools/cortex/scripts/validate-layout.sh --target tests/fixtures/layout-ok/
bash plugins/tools/cortex/scripts/validate-layout.sh --target tests/fixtures/layout-bad/ ; [[ $? -ne 0 ]] && echo OK

# Lint
bash plugins/tools/cortex/scripts/lint.sh --check tests/fixtures/lint/
bash plugins/tools/cortex/scripts/lint.sh --fix tests/fixtures/lint/
bash plugins/tools/cortex/scripts/lint.sh --check tests/fixtures/lint/   # 应退出 0

# Extract
bash plugins/tools/cortex/scripts/extract.sh --dry-run tests/fixtures/extract/
bash plugins/tools/cortex/scripts/extract.sh --apply tests/fixtures/extract/

# Plugin
python3 -c "import json; d=json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json')); assert len(d['skills'])==4 and len(d['agents'])==1, d"

# Skill frontmatter
for f in plugins/tools/cortex/skills/*/SKILL.md plugins/tools/cortex/agents/cortex.md; do
  python3 -c "import sys,yaml; c=open('$f').read().split('---'); y=yaml.safe_load(c[1]); assert y['name'] and y['description']" || echo "BAD: $f"
done
```

## Rollback 触发点

| 阶段 | 失败信号 | 回滚操作 |
| --- | --- | --- |
| Phase A | validate-layout.sh fixture 测试不通过 | 删 docs/layout.md + scripts/validate-layout.sh, 不进 B |
| Phase B | schema 文件 frontmatter 不合法 | 删对应 skills/ 子目录 |
| Phase C | lint/extract 脚本 fixture 不通过 | 删对应 skill + script + fixture |
| Phase D | plugin.json JSON 错 | `git checkout plugins/tools/cortex/.claude-plugin/plugin.json` |
| Phase E | 用户全盘驳回 G1 | 任务保持 in_progress, 回 Phase B 重做 schema |
| Phase F | E2E 链断 | 定位失败 phase, 回该 phase rollback |

## Dispatch Prompt 模板 (供 Phase B/C 派 sub-agent)

```
Active task: .trellis/tasks/06-09-cortex-kb-memory

目标: <subtask 目标行, 见 subtask/<id>.md>
已知: 读 prd.md + design.md + subtask/<id>.md
工作目录与范围: <见 subtask/<id>.md "资源" 节>
输出格式: 落盘到 <文件路径>, 完成后回报变更清单
验收标准: <见 subtask/<id>.md "验收" 节>
失败处理: 工具瞬时错误重试 1 次; 需要决策标 "需要: <问题>" 回 main
```
