# plan-diagnose: 诊断 .trellis 现状 (Phase A)

apply 前先诊断, 决定注入 / 更新 / 跳过。

## 诊断项

```bash
# 1. trellis 项目确认
ls .trellis/ || echo "非 trellis 项目"

# 2. 已注入 trellisx hook? (判断首次 apply vs 更新)
grep -q "trellisx-worktree" .trellis/config.yaml 2>/dev/null && echo "trellisx hook 已注入 (更新模式)" || echo "无 trellisx hook (首次 apply)"

# 3. spec 目录
ls .trellis/spec/ 2>/dev/null || echo "无 spec/, 将创建"

# 4. config.yaml (trellis 生命周期 hook 注入目标)
ls .trellis/config.yaml 2>/dev/null || echo "无 config.yaml, hook 注入将创建"

# 5. .gitignore worktrees 排除
grep -q ".worktrees/" "$(git rev-parse --show-toplevel)/.gitignore" 2>/dev/null && echo "已排除" || echo "需加 .worktrees/ 到 git 根 .gitignore"

# 6. task.py 可用 + worktree 已存在?
python3 .trellis/scripts/task.py current 2>/dev/null
git worktree list 2>/dev/null | grep ".worktrees" || echo "无 trellisx worktree"
```

## 诊断报告

输出:
```
trellisx-apply 诊断
───────────────────
- trellisx hook: 已注入 (更新模式) / 未注入 (首次 apply)
- 目标语言: zh / en ... (综合 $LANG locale + CLAUDE.md/README + 会话; 传给所有 writer 统一)
- spec/: 存在 / 待建
- config.yaml hooks: 已注入 worktree / 待注入
- .gitignore worktrees: 已排除 / 待加
```

## 模式判定

| 现状 | 模式 |
| --- | --- |
| config.yaml 无 trellisx hook | **首次 apply** — 全量注入 |
| config.yaml 已含 trellisx hook | **更新 apply** — 幂等覆盖脚本/配置到最新 |
| 缺 config.yaml | apply 创建 config.yaml 并注入 worktree hooks |

plan-diagnose 结果回传 main, 供 Gate 汇总 diff plan + 各 writer 参考。
