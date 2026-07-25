# PREFIX_RULE 多行三引号 — PRD (主入口)

## 目标

`hooks.py` 的 `_PREFIX_RULE` 当前用逐行 `"...\n"` 拼接 (每行一对引号)。改为单个三引号多行字符串, 去掉每行引号与 `\n` 拼接, 内容语义完全不变。

## 边界

- [ ] 仅改 `plugins/tools/skein/scripts/hooks.py:386` 的 `_PREFIX_RULE` 赋值。
- [ ] 渲染输出逐字节不变 (4 行文本, 首行 `# 回复前缀 (强制)`, 后 3 行 `- ` 列表)。
- [ ] 不动 `_task_phase_hints` 拼接逻辑 (`_PREFIX_RULE + _task_phase_hints(dir_)`)。

## 验收标准

- [ ] `_PREFIX_RULE` 为三引号多行字符串字面量, 无逐行引号拼接。
- [ ] `python3 -c "import ast; ast.parse"` 通过。
- [ ] import hooks 后 `_PREFIX_RULE` 值与旧写法逐字节一致 (4 行, 换行处正确)。

## 索引

- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list prefix-triple-quote`)
