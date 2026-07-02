# Implement — apply 注入异步等待清单

## Subtask 划分 (2 subtask, 并行, disjoint 文件集)

### S1: skill 表格重设 (owner: 文件集 A)
**文件** (disjoint):
- `plugins/tools/trellisx/skills/trellisx-flow/SKILL.md`
- `plugins/tools/trellisx/skills/trellisx-orchestrate/references/progress-communication.md`

**步骤**:
1. progress-communication.md §异步等待清单格式: 改 4 列 (id/状态/摘要/进度%), 状态加本地化说明 (中文进行中/等待中/阻塞; 英文 in_flight/pending/blocked; writer 按目标语言生成), 范例同步改
2. progress-communication.md 触发场景/不触发/与进度回传区别 段保留 (上一 task 加的, 仅表格部分改)
3. flow SKILL.md exec 阶段「异步等待 MUST 输出任务清单」段 + 硬规「其他必做」: 表格范例改 4 列; 不重复模板, 引用 progress-comm §格式
4. 两文件状态取值/列名/触发场景一致 (progress-comm 为 single source)

**自验**:
- `grep -c "进度%"` 两文件均 ≥1
- flow 不含完整表格模板 (仅引用)
- 两文件 4 列名一致

### S2: apply 注入维度新增 (owner: 文件集 B)
**文件** (disjoint):
- `plugins/tools/trellisx/skills/trellisx-apply/SKILL.md`
- `plugins/tools/trellisx/skills/trellisx-apply/references/workflow-injection.md`
- `plugins/tools/trellisx/skills/trellisx-apply/references/apply-verify.md`

**步骤**:
1. apply SKILL.md 注入维度表 (line 83-95 段) 加一行「异步等待清单」: 注入内容 = 异步等待输出 4 列表格规范; 落地 = workflow.md 注入点 2 (in_progress) + 注入点 3 (finish 限定)
2. workflow-injection.md 加:
   - 注入点 2 子段「异步等待清单 (in_progress)」: marker `trellisx:start/end:async-wait-in-progress`, 块末尾追加, 内容 = 触发场景 + 4 列表格模板 (writer 按目标语言填) + 状态本地化说明 + 引用 progress-comm
   - 注入点 3 子段「异步等待清单 (finish 限定)」: marker `trellisx:start/end:async-wait-finish`, 限定语境 = workflow 异步跑等 notification, 同表不同语境
3. apply-verify.md 加结构指纹断言:
   - marker key 存在: grep `trellisx:start:async-wait-in-progress` + `trellisx:start:async-wait-finish` (不依赖自然语言)
   - 列结构指纹: 注入 snippet 含 4 列占位 (id/状态/摘要/进度% 或本地化对等), 用 marker 包裹识别非词匹配

**自验**:
- apply SKILL.md 注入维度表含「异步等待清单」行
- workflow-injection.md 含两 marker key
- apply-verify.md 含两 marker key 断言

## 验证命令 (main 跑)

```bash
# 验 skill 表格识别
claude -p "读 <flow + progress-comm 路径>。问: 异步等待时输出表格几列? 列名? 状态取值如何本地化?" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'

# 验 apply 注入算法识别
claude -p "读 <workflow-injection.md>。问: apply 注入「异步等待清单」用哪几个 marker key? 注入点在哪?" --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

两 result 非空 + 含 4 列 / 两 marker key = 过。

## Rollback

文档变更, git stash 即可全回滚。无破坏性。
