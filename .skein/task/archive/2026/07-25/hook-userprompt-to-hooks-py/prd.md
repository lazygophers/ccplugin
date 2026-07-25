# UserPromptSubmit hook 迁 hooks.py 统一入口 — PRD (主入口)

## 目标
- [x] UserPromptSubmit hook 内容生产从 skein.py:Skein.user_prompt 迁到 hooks.py:cmd_user_prompt, 与其他 7 hook 统一入口
- [ ] plugin.json UserPromptSubmit hook 命令从 bin/skein user-prompt 改为 bin/skein-hooks user-prompt
- [ ] skein.py 删除 user_prompt 方法 + user-prompt 子命令注册 (3050/3113-3115) + 相关 import 若无其他引用则清
## 边界
- 范围: hooks.py 加 cmd_user_prompt + DISPATCH 注册 + plugin.json hook 命令改 + skein.py 删 user_prompt 及注册
- 范围外: hooks.py 现有 7 子命令不动
- 范围外: 不改 hook 注入文案内容 (文案刚在上 task 定稿)
- 已知约束: hooks.py 读 stdin JSON (hook_event_name+prompt), 非 skein.py 的 _read_hook_prompt 机制; cmd_user_prompt 需自取 prompt 字段 (但当前文案已不依赖 prompt 内容, 全交 AI 判)
## 验收标准
- [x] hooks.py 含 cmd_user_prompt 函数 + DISPATCH 注册 user-prompt
- [x] plugin.json UserPromptSubmit hook command = bin/skein-hooks user-prompt
- [x] skein.py 无 user_prompt 方法 + 无 user-prompt 子命令注册 (grep -c user_prompt == 0, 但 _uninit_ctx/_read_hook_prompt/budget_guard 若仅 user_prompt 用则一并清)
- [x] 注入文案与迁移前一致 (判 flow 标准 + 判定行格式 + 禁修饰词 + TaskCreate≠skein create + 自降级黑名单 + 查重 + AskUserQuestion)
- [x] 实测: echo JSON | bin/skein-hooks user-prompt 输出正确 additionalContext
- [x] python ast.parse hooks.py + skein.py 语法通过
- [x] claude -p 质量门 (端点抖则 hook 实测替代)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list hook-userprompt-to-hooks-py`)
