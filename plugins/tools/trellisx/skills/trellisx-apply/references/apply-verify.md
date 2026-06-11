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

[.trellis/spec/guides/trellisx-worktree.md] 仅新增 (已存在则跳过, 不覆盖)

[.trellis/scripts/trellisx-worktree.py] 创建 (生命周期 hook 调用)
  + [.trellis/config.yaml] hooks.after_start/after_archive 注入

[<git根>/.gitignore] + .worktrees/

影响: 跑完后 trellis 原生 hook 每轮注入 trellisx 规则; task.py start/archive 触发 config.yaml hooks 自适应建/销 worktree (微服务兼容)
```

## 2. 审批门 (强制)

用 `AskUserQuestion`:
```
question: "以上 trellisx-apply 变更是否写入 .trellis/ ?"
options:
  - 全部应用
  - 仅 workflow.md (跳过 worktree hook)
  - 取消
```

用户取消 → 0 变更退出。

## 3. 一次写盘

批准后按顺序:
1. `.trellis/workflow.md` (marker 注入, 见 workflow-injection.md 算法)
2. `.trellis/spec/guides/trellisx-worktree.md` (仅不存在时新增, 不动现有 spec)
3. `.trellis/scripts/trellisx-worktree.py` (创建) + `.trellis/config.yaml` hooks 注入
4. `<git根>/.gitignore` 追加 .worktrees/

## 4. 验证

```bash
# marker 注入成功
grep -c "trellisx:start:" .trellis/workflow.md      # 应 = 注入数
# workflow.md 仍合法 (trellis 能解析)
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "task.py 正常"
# spec 文件存在
ls .trellis/spec/guides/trellisx-worktree.md
# worktree 脚本可执行 + config.yaml hooks 可解析
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-worktree.py').read())" && echo "脚本语法 OK"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_start', get_hooks('after_start'))"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
```

## 4b. 流程闭环验证 (必须, 注入后确认完整闭环)

注入后, 验证 workflow.md 的任务执行流程是**完整闭环**: 从无任务 → 创建 → 规划 → worktree → 执行 → check → commit → finish 每个 status 衔接无断点。

```bash
# 1. 每个 workflow-state status 都存在 (trellis 原生 + trellisx 注入)
for st in no_task planning in_progress; do
  grep -q "\[workflow-state:$st\]" .trellis/workflow.md && echo "✓ $st 块在" || echo "✗ $st 缺"
done

# 2. trellisx 注入的 no_task/planning/in_progress marker 在对应块内 (不串位)
python3 - <<'EOF'
import re
s=open(".trellis/workflow.md").read()
for tag in ["no_task","planning","in_progress"]:
    m=re.search(rf"\[workflow-state:{tag}\](.*?)\[/workflow-state:{tag}\]", s, re.DOTALL)
    body=m.group(1) if m else ""
    key=tag.replace("-","_")
    ok = f"trellisx:start:{key}" in body
    print(f"{'✓' if ok else '✗'} trellisx:{key} marker 在 [{tag}] 块内")
EOF

# 2b. ★ no_task 原生文本未被替换 (规避踩坑根因: 只追加不替换)
grep -q "First classify the current turn" .trellis/workflow.md && echo "✓ no_task 原生分类文本在" || echo "✗ 危险: 原生被替换"
grep -q "task-creation consent" .trellis/workflow.md && echo "✓ no_task 原生征同意文本在" || echo "✗ 危险: 原生被替换"

# 3. 流程链完整: 注入内容引用的下游环节都存在
#    planning 提 subtask → in_progress 提 worktree+execute → 原生 check/finish
grep -q "subtask" .trellis/workflow.md && echo "✓ planning→subtask"
grep -q "worktree" .trellis/workflow.md && echo "✓ in_progress→worktree"
grep -qE "trellis-check|check" .trellis/workflow.md && echo "✓ →check 闭环"
grep -qE "finish|archive" .trellis/workflow.md && echo "✓ →finish 收尾"

# 4. 无断链: 注入未破坏 trellis 原生 Phase 流程 (Phase 1/2/3 仍在)
grep -cE "Phase [123]" .trellis/workflow.md
```

**闭环判定**: 上述全 ✓ = 流程完整闭环 (创建→规划→worktree→执行→check→finish 无断点)。任一 ✗ → 修复注入 (marker 串位 / 缺环节) 后重验, 直到闭环。

## 5. 完成报告

```
trellisx-apply 完成
───────────────────
注入 marker: N (workflow.md)
spec 文档: 已写
trellis hook: 已装 (config.yaml after_start/after_archive → worktree 自动化) / 跳过
gitignore: 已排除 .worktrees/ (git 根)
流程闭环: ✓ (create→planning→worktree→execute→check→finish 完整)

下一步: 重启会话 / reload 让 trellis hook 读到新 workflow.md。
之后 trellisx 规则由 trellis 原生机制注入, 无需 trellisx 运行时 hook。
```

## 回滚

写盘前 git stash backup:
```bash
git stash push -- .trellis/ 2>/dev/null
# 失败 → git stash pop 恢复; 成功 → git stash drop
```

## 幂等保证

重复 apply: workflow marker 替换 (不堆叠) + worktree spec 仅新增 (已存在跳过, 不动) + config.yaml hooks 检测 trellisx-worktree 已在则跳过 + 脚本覆盖更新。安全多次跑, 不破坏现有 spec。
