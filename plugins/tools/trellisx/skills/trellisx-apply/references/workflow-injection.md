# workflow.md 注入 (核心)

把 trellisx 规则注入 `.trellis/workflow.md` 的 workflow-state 块 + Phase 描述。trellis 原生 `inject-workflow-state` hook 每轮读这些块注入主会话, 所以规则写这里 = 每轮生效。

## 注入机制

全部注入用 marker 包裹, 幂等:
```
<!-- trellisx:start:<key> -->
<内容>
<!-- trellisx:end:<key> -->
```
重复跑: 找到同 key marker → 替换内容; 无则插入。

## 注入点 1: 顶部回复前缀规则

文件顶部 (第一个标题前) 插入:
```markdown
<!-- trellisx:start:prefix -->
> **trellisx 回复前缀**: 所有回复必须以 `[trellisx-{status}-{task-name}]` 开头 (无 active task 用 `[trellisx]`)。status = planning/in_progress/check/done/blocked。前缀置于回复最前。
<!-- trellisx:end:prefix -->
```

## 注入点 2: workflow-state 块 (trellis hook 每轮注入)

trellis 的 `[workflow-state:STATUS]...[/workflow-state:STATUS]` 块被 hook 按当前 status 注入。在对应块内追加 trellisx 规则 (marker 包裹):

### `[workflow-state:no_task]` 追加
```
<!-- trellisx:start:no_task -->
trellisx 任务门禁: 实施 (写盘/改文件) → 无条件建 task 走 planning; 探索 (纯只读) → 按复杂度决定。实施前必须 task.py create。
<!-- trellisx:end:no_task -->
```

### `[workflow-state:planning]` 追加
```
<!-- trellisx:start:planning -->
trellisx planning: 加载 trellisx-orchestrate skill。task 必须拆 ≥ 2 subtask, 每 subtask 独立文件 .trellis/tasks/<task>/subtask/<id>.md + mermaid 调度图。planning 完成进 task.py start 前确认 PRD/design/implement 齐备。
<!-- trellisx:end:planning -->
```

### `[workflow-state:in_progress]` 追加
```
<!-- trellisx:start:in_progress -->
trellisx 执行 (worktree 隔离, C1: main 可写但必在 worktree):
- task.py start 后已自动建 worktree .trellis/worktrees/<task> (平台 hook); 全部源码改动必须落该 worktree 内
- main 可直接写源码 (trellis inline 风格), 但目标路径必须在 worktree; 复杂/并行 subtask 派 sub-agent (isolation:worktree) 或 agent-team 成员
- 进 worktree: 写 worktree 绝对路径, 或 EnterWorktree 切会话
- 完成实施后必经 trellis-check (C3 闭环), 未过禁宣告完成
<!-- trellisx:end:in_progress -->
```

### `[workflow-state:in_progress-inline]` 追加 (codex inline 模式)
```
<!-- trellisx:start:in_progress_inline -->
trellisx inline: main 直接 edit, 但目标必须在 worktree .trellis/worktrees/<task> 内。完成后必经 trellis-check。
<!-- trellisx:end:in_progress_inline -->
```

## 注入点 3: Phase 描述 (前置流程铁律)

在 Phase 2 Execute 节开头追加:
```markdown
<!-- trellisx:start:phase2_order -->
### trellisx 前置流程铁律 (实施类, 禁跳步)

确认实施需求 → ① task.py create → ② planning (加载 trellisx-orchestrate, 拆 ≥ 2 subtask) → ③ task.py start (自动建 worktree) → ④ 在 worktree 内 execute (main 直写 worktree 路径 / 派 agent) → ⑤ trellis-check 闭环 → 完成。

禁: 直接写代码不建 task / 主工作区写源码 / 跳过 trellis-check。
<!-- trellisx:end:phase2_order -->
```

在 Phase 3 Finish 完成判定追加:
```markdown
<!-- trellisx:start:phase3_check -->
**trellisx 完成判定** (全满足才宣告 done):
- [ ] 全部 subtask done + 验收
- [ ] **trellis-check 综合验证通过 (C3 强制闭环)**
- [ ] 全部 worktree 已合并 + 移除 (.trellis/worktrees/<task> 清空)
- [ ] commit + 非平凡发现落 cortex
<!-- trellisx:end:phase3_check -->
```

## 注入算法 (apply 执行时)

```python
content = read(".trellis/workflow.md")
for key, snippet in injections.items():
    start, end = f"<!-- trellisx:start:{key} -->", f"<!-- trellisx:end:{key} -->"
    if start in content:                      # 已存在 → 替换 marker 内
        content = re.sub(f"{start}.*?{end}", f"{start}\n{snippet}\n{end}", content, flags=DOTALL)
    else:                                      # 不存在 → 插入到锚点后
        content = insert_after_anchor(content, key, f"{start}\n{snippet}\n{end}")
write(".trellis/workflow.md", content)
```

锚点定位: prefix → 文件首; no_task/planning/in_progress → 对应 `[workflow-state:X]` 块内末尾; phase → 对应 Phase 标题后。

## 重要: 不破坏 trellis 原生内容

- 只在 marker 内写, 绝不改 trellis 原生行
- workflow.md 是 trellis 模板生成 (`.template-hashes.json` 跟踪); 注入后 trellis update 可能覆盖 → 在 spec 留备份说明 (见 `spec-injection.md`), apply 可重跑
