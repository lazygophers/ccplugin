# Implement — trellisx 调度规约

## D1: task.md 锁 (交付 1)

- [ ] `.claude/settings.json` 加 permissions.deny Edit/Write .trellis/task.md
- [ ] 新建 `plugins/tools/trellisx/scripts/guard-taskmd.sh` (PreToolUse 拦截)
- [ ] `.claude/settings.json` 注册 PreToolUse hook (matcher Edit|Write)
- [ ] flow SKILL + workspace SKILL 加软约束 "禁直接编辑 task.md"

## D2: active_task.py 多 active (交付 2 核心)

- [ ] session 文件字段: 加 `active_tasks` 列表 (保留 `current_task` 作 focus)
- [ ] 向后兼容读: 旧单值 → 构造单元素列表
- [ ] `resolve_active_tasks` 新增 (复数, 返回全列表)
- [ ] `set_active_task` 改 add (检查上限 2)
- [ ] `clear_active_task` 改 remove 指定 task

## D3: task.py 命令改

- [ ] `cmd_current` 加 `--all` 选项列所有 active
- [ ] `cmd_start` 加入 active 集 (非顶替), 上限检查
- [ ] `cmd_finish` 从 active 集移除 focus, 切 focus
- [ ] `cmd_list` 标 active 标记

## D4: flow SKILL + scheduling.md 多 task 规约

- [ ] flow SKILL 加"多 task 并行调度"段 (active_tasks 概念, 上限 2, 冲突判定, focus)
- [ ] scheduling.md 加 task 级并行 (复用冲突算法, task 间 write-files/exec-scope)
- [ ] 反例黑名单加"超上限并行 / 直接编辑 task.md"

## D5: 质检 + 回归

```bash
# A. task.md 锁
# AI 试 Edit .trellis/task.md → 应被 deny 拒
# hook 跑: bash plugins/tools/trellisx/scripts/guard-taskmd.sh 测

# B. 多 active 回归
python3 ./.trellis/scripts/task.py create "test A" --slug test-a
python3 ./.trellis/scripts/task.py create "test B" --slug test-b
python3 ./.trellis/scripts/task.py start test-a
python3 ./.trellis/scripts/task.py start test-b
python3 ./.trellis/scripts/task.py current --all  # 应列 [test-a, test-b]
python3 ./.trellis/scripts/task.py finish  # 移除 focus
python3 ./.trellis/scripts/task.py current --all  # 应列剩 1
# 上限测: start 第三个应报错

# C. 旧文件兼容
# 手造单值 session 文件, current 应能读

# D. claude -p
claude -p "读 flow SKILL + scheduling.md。多 task 怎么并行? task.md 怎么编辑?" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

## Rollback

- settings.json / hook / SKILL 改动 → git checkout
- active_task.py / task.py 改动 → git checkout (核心脚本, 回滚前确认无 session 数据破损)
- test-a/test-b task → archive 清理
