# worktree 启用态全链路 gate — PRD (主入口)

## 目标
`use_worktree` 配置在**全链路**一致生效, 禁用态下 worktree 概念彻底消失:
- [ ] 禁用时 task 的 worktree/repos 是**禁止填写**项 (create/repos 直接拒), 前端/看板/CLI/API **不展示**, start **不自动创建**。
- [ ] SessionStart 与 UserPromptSubmit 都注入当前 **worktree 启用/禁用态** + **最大并行 subtask 数 (max_active)**。
- [ ] 自动建 worktree 只在 git 目录 (含子目录独立 git 仓)。

## 边界
- [ ] 真值来源唯一: 默认值只在 `skein.py CONFIG_DEFAULTS` (max_active=2, use_worktree=true)。**hook/插件禁硬编码默认值**, 缺值从 `skein.CONFIG_DEFAULTS` 取。
- [ ] 不改 `max_active` 语义 (仍是唯一并发键, 兼作 task 级上限 + subtask claim 池)。
- [ ] Req6 (git-only 自动建) 现状已满足 (`start` 单根走 `self.git and use_worktree`; `--repos` 走 `_mkwt` 校验各子仓 git 顶层) — 本任务仅补验证/测试, 不改逻辑。

## 验收标准
### R1 禁填 (use_worktree=false)
- [ ] `create --repos <x>` 当 use_worktree=false → 直接 `SystemExit` 拒 (不落 repos)。
- [ ] `repos <tid> --set <x>` 当 use_worktree=false → 直接 `SystemExit` 拒。
- [ ] 启用态下 create/repos 行为不变。

### R2 不展示 (use_worktree=false)
- [ ] 禁用态下这些出口不显示 worktree 段: `session_context`(1528)、`current`(1005)、`status`(1061)、task.md 看板列(1577/1590/1598)、`_brief`(1087)、`_board_data`(2070)。
- [ ] 前端 `board-render.js:360` / `board.js:317`: worktree 行仅在真值时渲染 (禁用态 null → 不渲染)。
- [ ] 启用态展示不变。

### R3 注入 (两个 hook)
- [ ] `session_context()` (SessionStart) 注入行: worktree 启用/禁用态 + 最大并行 subtask 数。
- [ ] `cmd_user_prompt()` (UserPromptSubmit, hooks.py) 注入同上; 值经 `skein.CONFIG_DEFAULTS` 兜底, **不硬编码 2/true**; 读 config.yaml + ENV override 同 `config()`。

### 门禁
- [ ] `tests/test_config_cli.py` + 新增禁用态测试全绿。
- [ ] `python3 -c "import ast; ast.parse(...)"` 两脚本通过。
- [ ] Req6: 加测试证明非 git 目录不建 worktree、子 git 仓可建。

## 索引
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list worktree-config-gate`)
