# 回复前缀规则多行化

## 目标

`_PREFIX_RULE` (hooks.py:386) 当前是单行挤压串, 可读性差。改为多行 bullet 文本:

```
# 回复前缀 (强制)
- [ ] 每条回复以 `[skein]` 开头
- [ ] 正在处理某 task 时改用 `[skein|<taskId>|<阶段>]`
- [ ] 阶段取值: plan / exec / check / research
```

skein.py:1526 平行注入的同一规则内联行同步为多行 (两注入点文案一致)。

## 边界

- [ ] 只改 `plugins/tools/skein/scripts/hooks.py` (_PREFIX_RULE) 与 `plugins/tools/skein/scripts/skein.py` (session_context 内联前缀规则行, ~1526)。
- [ ] 纯文案/格式改动, 不改注入逻辑、不改 _task_phase_hints / prefix_tasks 计算、不改语义 (仍强制 [skein] 前缀 + task 内改 [skein|id|阶段])。
- [ ] 阶段取值集合不变 (plan/exec/check/research)。

## 验收标准

- [ ] `_PREFIX_RULE` 渲染为多行: 首行 `# 回复前缀 (强制)`, 后接 3 条 `- ` bullet (含 `[skein]` 开头 / `[skein|<taskId>|<阶段>]` / 阶段取值)。
- [ ] skein.py:1526 内联前缀规则行同步为等价多行文本 (与 _PREFIX_RULE 语义一致)。
- [ ] `python3 -c "import ast; ast.parse(...)"` 两文件语法通过。
- [ ] hooks.py: `python3 -c "import hooks; print(hooks._PREFIX_RULE)"` 打印多行 (含 3 个换行)。
- [ ] 现有 hook 测试 (test_reply_prefix.py 若断言前缀规则文本) 跟进不破; `uv run --with pytest python -m pytest .../test_reply_prefix.py -q` 全绿。

## 索引

- [ ] 实现: `plugins/tools/skein/scripts/hooks.py:386` _PREFIX_RULE + `skein.py:1526` 内联
- [ ] 测试: `plugins/tools/skein/scripts/tests/test_reply_prefix.py`
