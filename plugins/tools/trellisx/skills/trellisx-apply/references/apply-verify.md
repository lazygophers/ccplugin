# 步骤 5: 审批 + 写盘 + 验证

收集步骤 2-4 的全部注入, 走审批门, 一次写盘, 验证。

## 1. 汇总变更 plan

展示给用户 (不写盘):
```
trellisx-apply 变更计划
───────────────────────
模式: 首次 apply / 更新 apply

[workflow.md] 注入 / 更新 marker:
  + trellisx:prefix (回复前缀)
  + trellisx:no_task / planning / in_progress / in_progress_inline
  + trellisx:phase2_order / phase3_check

[.trellis/spec/guides/trellixx-conventions.md] 创建 / 覆盖

[.claude/hooks/trellisx-worktree.py] 创建 (PostToolUse 自动 worktree)
  + 平台 hook 注册 (PostToolUse Bash)

[<git根>/.gitignore] + .worktrees/

影响: 跑完后 trellis 原生 hook 每轮注入 trellisx 规则; task.py create/start 自适应建 worktree (微服务兼容)
```

## 2. 审批门 (强制)

用 `AskUserQuestion`:
```
question: "以上 trellisx-apply 变更是否写入 .trellis/ ?"
options:
  - 全部应用
  - 仅 workflow.md (跳过平台 hook)
  - 取消
```

用户取消 → 0 变更退出。

## 3. 一次写盘

批准后按顺序:
1. `.trellis/workflow.md` (marker 注入, 见 workflow-injection.md 算法)
2. `.trellis/spec/guides/trellixx-conventions.md` (覆盖)
3. `.claude/hooks/trellisx-worktree.py` (创建) + 平台 hook 注册
4. `<git根>/.gitignore` 追加 .worktrees/

## 4. 验证

```bash
# marker 注入成功
grep -c "trellisx:start:" .trellis/workflow.md      # 应 = 注入数
# workflow.md 仍合法 (trellis 能解析)
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "task.py 正常"
# spec 文件存在
ls .trellis/spec/guides/trellixx-conventions.md
# 平台 hook 可执行
python3 -c "import ast; ast.parse(open('.claude/hooks/trellisx-worktree.py').read())" && echo "hook 语法 OK"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
```

## 5. 完成报告

```
trellisx-apply 完成
───────────────────
注入 marker: N (workflow.md)
spec 文档: 已写
平台 hook: 已装 (worktree 自动化) / 跳过 (无 .claude/hooks)
gitignore: 已排除 .worktrees/ (git 根)

下一步: 重启会话 / reload 让 trellis hook 读到新 workflow.md。
之后 trellisx 规则由 trellis 原生机制注入, 无需 trellisx 运行时 hook。
```

## 回滚

写盘前 git stash backup:
```bash
git stash push -- .trellis/ .claude/hooks/ 2>/dev/null
# 失败 → git stash pop 恢复; 成功 → git stash drop
```

## 幂等保证

重复 apply: marker 替换 (不堆叠) + spec/hook 覆盖。安全多次跑。
