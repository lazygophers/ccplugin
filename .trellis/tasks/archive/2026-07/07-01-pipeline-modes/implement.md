# Implement — novelist-pipeline 多场景执行清单

## D1: SKILL.md 入参契约 + mode 路由

改 `plugins/tools/novelist/skills/novelist-pipeline/SKILL.md`:

- [ ] frontmatter description 加 mode 维度 (默认 write, 支持 review/humanize/proofread/polish/rewrite/outline)
- [ ] argument-hint 改: `[mode] [写到第N章|写N章] [--workflow|--no-workflow]（mode 缺省=write）`
- [ ] 新增「mode 入参」段: 7 mode 表 (mode/级/前置/行为/子mode默认/载体默认)
- [ ] 新增「载体选择」段: write 默认 Workflow, 其余默认 subagent, --workflow/--no-workflow 覆盖规则表
- [ ] 「激活时执行」改: step 0 加 mode 解析 + 载体选择; step 4 按 mode 选 Workflow 或 subagent 编排
- [ ] 新增「subagent 编排路径」段: 非 workflow 时 main 怎么 DAG 调度 (派 general-purpose Agent × 章, 并发2, 引用 trellisx scheduling 语义)
- [ ] 中文别名表 (评审/去AI味/校对/润色/重写/大纲)
- [ ] 保留现有 write 架构/评分/反例段 (mode=write 时仍适用)

## D2: workflow.js mode 分支

改 `plugins/tools/novelist/skills/novelist-pipeline/workflow.js`:

- [ ] 加 `const MODE = _args.mode || "write"`
- [ ] 加 `needsPhase(mode, phase)` 映射 (design.md 路径 A 表)
- [ ] 主流程各 phase 加 mode 守卫: `if (!needsPhase(MODE, "phase名")) continue/skip`
  - ensureRouteMap: mode=outline 或 write 才跑
  - updateWorldview/preCheck: 仅 write
  - writer: 仅 write (或 polish 不跑)
  - finishChain: write 全跑; polish 跳 write 只跑三环+fix+定稿; review 只跑 checker; humanize 只跑 humanizer(+fix); proofread 只跑 proofer(+fix)
  - unifiedCheck: write/review/polish/rewrite 跑
- [ ] meta.phases 按 mode 动态? (可选, 静态全列也行)
- [ ] **write 路径零改动** (MODE=write 时所有 needsPhase 返回 true)

验证 write 零回归:
```bash
# 语法
node --check plugins/tools/novelist/skills/novelist-pipeline/workflow.js
```

## D3: SKILL.md subagent 编排路径描述

- [ ] 描述 main 解析 mode → 章节范围 → DAG 派 Agent (general-purpose, prompt 指示调 novelist-<skill>)
- [ ] 并发上限 2 (章间文件不相交可并行)
- [ ] 统一 check 串行末尾 (若 mode 需要)
- [ ] Agent prompt 6 字段模板 (引用 trellisx dispatch 规约)
- [ ] 失败处理: subagent 标 `需要:` → main 转达

## D4: 质检

```bash
# A. workflow.js 语法
node --check plugins/tools/novelist/skills/novelist-pipeline/workflow.js

# B. claude -p 验 mode 路由 + 载体识别 (3 场景)
claude -p "读 novelist-pipeline SKILL.md。场景1: /novelist-pipeline (空) 场景2: /novelist-pipeline review 30-35 场景3: /novelist-pipeline humanize 5 --workflow。各走什么载体?" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'

# C. novelist-lint 跑 (SKILL.md frontmatter 改后仍合规)
python3 plugins/tools/novelist/skills/novelist-lint/scripts/lint.py --plugin-dir plugins/tools/novelist
```

## D5: 自检

- [ ] mode 解析: write(缺省)/review/humanize/proofread/polish/rewrite/outline 各能识别
- [ ] 载体选择: write→Workflow, review→subagent, review --workflow→Workflow, write --no-worktree→subagent
- [ ] workflow.js MODE=write 时 needsPhase 全 true (零回归)

## 验证命令汇总

- node --check workflow.js 通过
- claude -p 3 场景返回正确 mode+载体
- novelist-lint 全 PASS (SKILL.md frontmatter 合规)

## Rollback

- SKILL.md / workflow.js 改动 → `git checkout -- <file>`
- 纯文档+脚本, 无破坏性操作
