# 输出格式规范

## 所有输出必须包含前缀

**格式**：`[flow·{task_id}·{state}]`

### 说明

- **task_id**：任务唯一标识
- **state**：当前状态名称（explore/align/plan/exec/verify/done/cancel/pending）

### 应用范围

1. **Skill 输出**：所有返回给用户的内容
2. **Agent 输出**：所有 Agent 调用的结果
3. **日志输出**：所有进度、状态、错误信息
4. **文件输出**：写入 task.json、align.json 等时的注释

### 示例

```python
# 输出到对话
print(f"[flow·{task_id}·{state}] 任务已完成")

# 返回结果
return {
    "output": f"[flow·{task_id}·{state}] 执行结果",
    "status": "completed"
}

# 写入文件
comment = f"# [flow·{task_id}·{state}] Generated at {now()}"
```

### 检查清单

所有 skills/agents 必须在输出部分包含：
- [ ] 所有用户可见输出带前缀
- [ ] 所有返回结果带前缀
- [ ] 所有日志信息带前缀
- [ ] 所有错误信息带前缀
