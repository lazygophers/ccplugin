# hooks.py 适配 + fileMatch 注入 + 修两现存 bug — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] `hooks.py` 的 spec 元数据校验跟上新模型 (`namespace` / `inclusion`), 否则每次写 spec 文件都误报
- [ ] **修两个现存 bug** (发现于本轮勘察, 与迁移在同一路径上, 顺手修):
      1. `hooks.py:177` `SPEC_REQUIRED` 含 `created` 要求 unix ts, 但 `spec.py` 模块 docstring 明确「时间类字段一律不写」→ **每次写 spec 文件都误告警**
      2. `hooks.py:178` `SPEC_LAYERS = ("core","recall")` 漏 `external` → **写 external 层文件必报「非法 layer」**
- [ ] **落地第四种加载策略 `fileMatch`** — 规则声明 `globs`, 编辑匹配文件时自动注入该页正文。这是 skein 现在完全缺失的一档 (对齐 Kiro `inclusion: fileMatch` / Cursor Auto Attached)
- [ ] 成功长什么样: 写 spec 文件不再误告警; 改 `scripts/*.py` 时对应领域约定自动进上下文, 不必塞 `always` 浪费常驻预算、也不靠 `auto` 召回撞运气

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `scripts/hooks.py` 的 `cmd_spec_meta` / `cmd_guard` / `cmd_stop_check` 三处适配
- [ ] 范围内: fileMatch 注入逻辑 (挂在**已有的** `cmd_guard` 上, `plugin.json` 接线零改动)
- [ ] 范围外: `spec.py` 模型层 (归 `spec-model-core`, 本 task 依赖其完成)
- [ ] 范围外: 用户级 (`~/.skein`) fileMatch —— **明确不做**, 见约束
- [ ] 约束: 依赖 `spec-model-core` 已落地
- [ ] 约束: **只做工作区级 fileMatch, 不做用户级** —— Kiro 的 fileMatch 在全局 steering 目录下静默不生效 (github.com/kirodotdev/Kiro/issues/9176), 根因是 glob 没有 workspace root 可解析。绕开这个雷
- [ ] 约束: hook 全部非阻塞 —— spec 元数据问题只出 warning, 禁阻断用户的 Write/Edit
- [ ] 约束: `cmd_guard` 已挂 `PreToolUse` matcher `Edit|Write|MultiEdit|Read` 且 timeout 5s, 注入逻辑不得让它超时
- [ ] 约束: 纯 stdlib

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] `SPEC_REQUIRED` 改为 `("title","namespace","inclusion","keywords")` —— **`created` 已移除**, 写一个无 `created` 字段的 spec 文件不再告警
- [ ] `SPEC_LAYERS` 改为 `SPEC_INCLUSIONS = ("always","auto","fileMatch","manual")`; 写 `inclusion: manual` 的 external 页**不再**报非法
- [ ] `namespace` 只校验非空, **不校验白名单** (namespace 开放可扩展); 自建 namespace 的页不告警
- [ ] `inclusion: fileMatch` 但缺 `globs` → 告警 (warning, 非阻塞)
- [ ] `namespace: product|map` 缺 `anchors` → 告警 (warning, 非阻塞, 因失效检测依赖它)
- [ ] `cmd_guard` 新增: `tool_input.file_path` 与各 `inclusion: fileMatch` 页的 `globs` 匹配 → 该页正文经 `additionalContext` 注入
- [ ] fileMatch 匹配用 `fnmatch`/`pathlib.PurePath.match` (stdlib), glob 相对**工作区根**解析
- [ ] 无 `fileMatch` 页时 `cmd_guard` 行为与改前完全一致 (零回归)
- [ ] `cmd_guard` 在 spec 库有 50 页规模下单次执行 < 1s (远离 5s timeout)
- [ ] `cmd_guard` 原有职责 (硬阻 AI 直读写 task.json / task.md) 完全保留, 现有用例全绿
- [ ] `cmd_stop_check` 跟随 `maintain` 判据分表: `product` namespace 的失效项**不写** `.pending-fix` (不自动修需求真值)
- [ ] 新增用例覆盖: 两个 bug 的回归 / fileMatch 命中与未命中 / 缺 globs 告警 / product 不写标记 / guard 原职责不回归
- [ ] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-hooks-adapt`)
