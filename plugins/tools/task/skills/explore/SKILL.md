---
description: 现状探索，收集当前上下文信息并构建理解
memory: project
color: orange
model: sonnet
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:explore
---

# Explore Skill

## 执行流程

> 目标导向的渐进式探索，聚焦任务相关上下文

```python
# 检查是否已有探索结果
context_file = f".lazygophers/tasks/{task_id}/context.json"
existing_context = read_json(context_file) if exists(context_file) else None

# 阶段1：任务相关性分析（<1分钟）
keywords = extract_from(user_prompt)
target_modules = search_relevant(keywords)

# 阶段2：目标范围探索（<3分钟）
for module in target_modules:
    files = locate_module_files(module)
    for file in files:
        patterns = extract_code_patterns(file)
        style = analyze_coding_style(file)

# 阶段3：现有实现风格（<2分钟）
naming_conventions = deduce_naming()
indentation = detect_indent_style()
import_patterns = analyze_imports()
error_handling = analyze_error_patterns()

# 合并或更新上下文
new_context = {
    "task_related": {
        "modules": target_modules,
        "files": target_files,
        "patterns": code_patterns
    },
    "code_style": {
        "naming": naming_conventions,
        "indentation": indentation,
        "imports": import_patterns,
        "error_handling": error_handling
    },
    "last_updated": now()
}

# 如果有旧上下文，增量更新而非覆盖
if existing_context:
    merged = merge_context(existing_context, new_context)
    write_json(context_file, merged)
else:
    write_json(context_file, new_context)
```

## 检查清单

### 任务相关性
- [ ] 任务关键词已提取
- [ ] 相关模块已定位（非全项目）
- [ ] 目标文件已筛选

### 实现风格
- [ ] 命名约定已识别（camelCase/snake_case/PascalCase）
- [ ] 缩进风格已检测（空格/tab，2/4/8）
- [ ] 导入模式已分析
- [ ] 错误处理模式已提取

### 上下文管理
- [ ] 已有 context.json 已检查
- [ ] 增量更新而非覆盖（如有旧数据）
- [ ] 时间戳已更新

### 输出
- [ ] context.json 已写入 `.lazygophers/tasks/{task_id}/context.json`

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（explore）
