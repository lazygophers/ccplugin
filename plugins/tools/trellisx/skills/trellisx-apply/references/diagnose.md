# 步骤 1: 诊断 .trellis 现状

apply 前先诊断, 决定注入 / 更新 / 跳过。

## 诊断项

```bash
# 1. trellis 项目确认
ls .trellis/workflow.md || echo "缺 workflow.md"

# 2. 已有 trellisx marker (判断首次 apply vs 更新)
grep -c "trellisx:start:" .trellis/workflow.md 2>/dev/null

# 3. workflow-state 块清单 (确认注入锚点存在)
grep -oE "\[workflow-state:[a-z_-]+\]" .trellis/workflow.md | sort -u

# 4. spec 目录
ls .trellis/spec/ 2>/dev/null || echo "无 spec/, 将创建"

# 5. config.yaml (trellis 生命周期 hook 注入目标)
ls .trellis/config.yaml 2>/dev/null || echo "无 config.yaml, hook 注入将创建"
grep -q "trellisx-worktree" .trellis/config.yaml 2>/dev/null && echo "worktree hook 已注入" || echo "worktree hook 待注入"

# 6. .gitignore worktrees 排除
grep -q ".worktrees/" "$(git rev-parse --show-toplevel)/.gitignore" 2>/dev/null && echo "已排除" || echo "需加 .worktrees/ 到 git 根 .gitignore"

# 7. task.py 可用 + worktree 已存在?
python3 .trellis/scripts/task.py current 2>/dev/null
git worktree list 2>/dev/null | grep ".worktrees" || echo "无 trellisx worktree"
```

## 诊断报告

输出:
```
trellisx-apply 诊断
───────────────────
- workflow.md: 存在 / 缺失
- 已有 trellisx marker: N 个 (0 = 首次 apply, >0 = 更新模式)
- workflow-state 块: [no_task] [planning] [in_progress] [in_progress-inline] ... (注入锚点)
- spec/: 存在 / 待建
- config.yaml hooks: 已注入 worktree / 待注入
- .gitignore worktrees: 已排除 / 待加
```

## 模式判定

| 现状 | 模式 |
| --- | --- |
| 0 个 trellisx marker | **首次 apply** — 全量注入 |
| > 0 个 marker | **更新 apply** — 替换 marker 内容到最新 (幂等) |
| 缺 workflow-state 锚点块 | 警告: trellis 版本可能不兼容, 注入到 Phase 描述兜底 |
| 缺 config.yaml | apply 创建 config.yaml 并注入 worktree hooks |

诊断完进步骤 2 (workflow 注入)。
