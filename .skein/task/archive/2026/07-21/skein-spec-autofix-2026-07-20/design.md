# skein-spec-autofix — 详细设计

## 用户确认 (2026-07-20, 3 轮 AskUserQuestion)

- **目标**: SKEIN 过程中发现 spec 问题全自动修复, agent bg 异步, 不让人介入
- **载体**: Stop hook 检测 → 写 `.skein/spec/.pending-fix` 标记 → main 检测标记 → 派 skein-specer agent bg 执行
- **范围**: 4 类全修(超预算降级 + stale 归档 + keywords 重复归档 + 断链/废弃归档)
- **安全**: 记审计日志 `.skein/spec/.audit-log`(可追溯不停顿)
- **降级粒度**: 降到合格即停(core < 8000)
- **机制**: 1+2+3 全做 — prune 加超预算判据 + maintain --apply 标志 + degrade 子命令

## 召回注入 (recaller)

- `git/reconstruct-56` 变更自动 commit(禁 push) — auto-fix 后自动 commit 同源
- `arch/reconstruct-38` 写入口唯一 — spec 修复单一入口(spec.py)
- `impl/sediment-60` 硬护栏范式 — 安全门槛设计
- `impl/sediment-62` 单变量轮 — 降级一次一条验证再降

## 架构 / 数据流

```
agent 回合结束
  ↓
Stop hook (skein-hooks stop-check)
  ↓ 跑 maintain 快查(只检测, 不修)
  有问题 → 写 .skein/spec/.pending-fix (JSON: 类型+文件列表+时间戳)
  ↓
main 下回合 SessionStart 或 user-prompt 检测标记
  ↓ 标记存在
派 skein-specer agent bg (fire-and-forget)
  ↓
specer 读标记 → 跑对应修复:
  - 超预算 → degrade(降最大文件 core→recall, 合格即停)
  - stale → archive
  - keywords 重复 → archive(保留最新)
  - 断链/废弃 → archive
每步写 .audit-log(ts + 动作 + 文件 + 前/后)
  ↓
reindex + 清标记
```

## spec.py 改动 (核心)

### 1. prune 加超预算判据
- 现 prune 判据: stale / keywords 重复 / 断链 / 废弃
- 加: core 超预算 → 降级 top-1(最大文件)core→recall, reindex, 重新检测, 仍超再降(循环到合格)
- 降级动作 = git mv + frontmatter layer 改 + reindex

### 2. maintain --apply 标志
- 现 maintain: 只报告
- 加 `--apply`: 执行所有可自动修复项(超预算降级 + stale/重复/废弃归档), 断链只报告(需人判断修哪头)
- 默认(无 --apply)不变, 保手动口

### 3. degrade 子命令
- `skein-spec degrade <file>`: 显式降级单文件 core→recall
- `skein-spec degrade --auto`: 自动模式(降到合格即停)
- 被 prune/maintain --apply 内部复用

### 4. 审计日志
- `.skein/spec/.audit-log` 追加写: `{ts}|{action}|{file}|{before}->({after})|{reason}`
- fire-and-forget, 不阻塞
- **日志轮转: 最多保留 7 天**(用户约束 2026-07-20)。每次写日志前先清 7 天前的行(按 ts 字段判), 防 .audit-log 无限增长

## hooks.py 改动

### 新增 cmd_stop_check (Stop hook)
- 跑 `skein-spec maintain --check-only`(快查, 不修, 只产出问题清单)
- 有问题 → 写 `.skein/spec/.pending-fix`(JSON)
- 无问题 → 不写(零开销)
- timeout 短(maintain 快查应 <3s)

## plugin.json 改动

加 Stop hook:
```json
"Stop": [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/bin/skein-hooks stop-check", "timeout": 5}]}]
```

## skill / agent 改动

- `skein-spec` SKILL.md: 加 auto-fix 模式说明(Stop 触发 + agent bg)
- `skein-specer` agent.md: 加「读 .pending-fix 标记 → 执行修复」职责
- `skein-finish` SKILL.md: finish 后也检测标记(双保险, 防 Stop hook 漏)

## subtask 拆解

1. **spec-core-impl**: spec.py 加 degrade 子命令 + prune 超预算判据 + maintain --apply + 审计日志(核心逻辑)
2. **hook-stop-check**: hooks.py 加 cmd_stop_check + plugin.json 加 Stop hook
3. **agent-skill-update**: skein-specer agent.md + skein-spec/skein-finish SKILL.md 更新
4. **test-autofix**: 写 test 验证 4 类修复 + 标记流转 + 审计日志(用 skein 的 test_skein.py 模式)

## 验证

- 单元: spec.py 各新命令(degrade/prune超预算/maintain --apply)test
- 集成: 模拟超预算 → 跑 Stop hook → 验证标记写出 → 模拟 specer 读标记修复 → 验证降级 + 审计日志
- claude -p 质检门(CLAUDE.md 强制, 改了 SKILL.md / agent.md)
