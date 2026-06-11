# workflow.md 注入 (纯增量, 只加 worktree + subtask)

把 **worktree 隔离** + **subtask 拆分** 两个维度增量注入 `.trellis/workflow.md`。trellis 原生 `inject-workflow-state` hook 每轮读这些块, 注入内容随之生效。

## 核心原则: 不修改 trellis 原生流程

**apply 只增加 2 个维度 (worktree + subtask), 绝不碰 trellis 原生的 task 创建 / check / finish / 前缀逻辑。**

- ✅ 注入: `[workflow-state:planning]` 加 subtask 拆分 / `[workflow-state:in_progress]` 加 worktree 隔离
- ❌ **禁注入**: `[workflow-state:no_task]` (会干扰 trellis 原生 task 创建触发) / Phase 流程重写 / 完成判定 / 前缀标记
- 注入方式: 在 workflow-state 块**原生内容之后追加** marker, 绝不替换 / 覆盖原生文本

> 教训: 早期版本注入 no_task 块 + 重写 Phase 流程, 导致 trellis 原生 task 创建不再触发。apply 必须最小侵入。

## 注入机制 (marker 幂等)

```
<!-- trellisx:start:<key> -->
<内容>
<!-- trellisx:end:<key> -->
```
重复跑: 同 key marker → 替换内容; 无 → 在锚点块**末尾**追加 (原生内容之后)。

## 注入点 1: `[workflow-state:planning]` 块末尾追加 subtask

```
<!-- trellisx:start:planning -->
trellisx (增量): 任务规划时拆 >= 2 subtask, 每 subtask 独立文件 .trellis/tasks/<task>/subtask/<id>-<slug>.md + PRD 内 mermaid 调度图。**调度图必须显式标出并行组**: 无依赖的 subtask 归同一并行批次 (同时跑), 有依赖的标依赖箭头。拆分目标 = 最大化可并行的 subtask 数, 缩短关键路径。详见 trellisx-orchestrate skill。
<!-- trellisx:end:planning -->
```

## 注入点 2: `[workflow-state:in_progress]` 块末尾追加 worktree

```
<!-- trellisx:start:in_progress -->
trellisx (增量): 本 task 改动隔离在 worktree (git 根 .worktrees/<worktree>, 平台 hook 自适应建, 微服务自动 sparse)。源码写盘目标用该 worktree 路径。

**异步并行硬规 (降低总开发时长)**: 按调度图执行, 无依赖的 subtask **必须在同一条回复里一次性发起多个 sub-agent 调用** (Claude Code 同一消息多个 Agent tool = 真并行同时跑); **禁逐个串行派** (串行 = 各 subtask 耗时叠加, 违背提效)。有依赖的 subtask 等上游 done 再派下游。每个写盘 sub-agent 带 isolation:worktree。收到各 agent 返回立即回传用户进度。task archive 时 worktree 干净则自动销毁。
<!-- trellisx:end:in_progress -->
```

## 注入点 3: `[workflow-state:in_progress-inline]` 块末尾 (codex inline)

```
<!-- trellisx:start:in_progress_inline -->
trellisx (增量): inline 模式 main 直接 edit, 但源码目标路径必须在 worktree (.worktrees/<worktree>) 内。
<!-- trellisx:end:in_progress_inline -->
```

## 注入算法

```python
content = read(".trellis/workflow.md")
INJECT = {  # 只这 3 个 key, 不碰 no_task / Phase / 完成判定
    "planning": planning_snippet,
    "in_progress": in_progress_snippet,
    "in_progress-inline": in_progress_inline_snippet,
}
for tag, snippet in INJECT.items():
    key = tag.replace("-", "_")
    start, end = f"<!-- trellisx:start:{key} -->", f"<!-- trellisx:end:{key} -->"
    if start in content:                          # 已注入 -> 替换 marker 内
        content = re.sub(f"{start}.*?{end}", f"{start}\n{snippet}\n{end}", content, flags=re.DOTALL)
    else:                                          # 未注入 -> 在该 workflow-state 块原生内容之后插入
        m = re.search(rf"(\[workflow-state:{tag}\].*?)(\n\[/workflow-state:{tag}\])", content, re.DOTALL)
        if m:
            content = content[:m.end(1)] + f"\n{start}\n{snippet}\n{end}" + content[m.end(1):]
        # 块不存在 -> 跳过 (不强行创建, 不破坏原生)
write(".trellis/workflow.md", content)
```

## 验证 (确保没破坏原生)

```bash
# 原生 workflow-state 标签配对 (起始 = 结束数)
grep -c "\[workflow-state:" .trellis/workflow.md
grep -c "\[/workflow-state:" .trellis/workflow.md
# no_task 块原生内容未被动 (无 trellisx marker)
grep -A5 "\[workflow-state:no_task\]" .trellis/workflow.md | grep -c "trellisx"   # 应 = 0
# task.py 创建流程未坏
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "task.py OK"
```

## 不破坏 trellis 原生

- 只在 planning / in_progress 块**末尾追加** marker, 原生行一字不改
- **绝不碰 no_task 块** (task 创建触发是 trellis 原生职责)
- workflow.md 被 trellis update 覆盖后, 重跑 apply 恢复注入 (幂等)
