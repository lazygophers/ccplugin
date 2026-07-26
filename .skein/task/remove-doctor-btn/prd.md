# 移除前端 doctor 命令快捷条 — PRD (主入口)

## 目标
- [ ] 移除 board 页顶部命令快捷条 (cmd-bar) 整套前端。doctor 是其唯一按钮, 用户要求移除前端相关部分。
- [ ] 成功: 打开 web 看板, 顶部不再有 doctor 按钮/命令快捷条/命令输出区。

## 边界
范围内:
- [ ] `assets/webapp/src/pages/board.js`: 删 `.cmd-bar`/`.cmd-btn`/`.cmd-out` CSS (159-167)、`wireCmdBar` 函数及注释 (508-548)、`render` innerHTML 里 cmd-bar/cmd-out 片段 (557-560)、`wireCmdBar(mount, ctx)` 调用 (574)。

范围外 (非目标):
- [ ] 后端 `skein.py` 的 `doctor` 命令/`_exec_argv` 白名单保留 (start 前置体检仍用 doctor)。
- [ ] `api.js` 的 `exec` 通用方法保留 (泛用, 非 doctor 专属)。
- [ ] 不动其他页面/组件。

已知约束:
- [ ] `esc()` 若仅 cmd-bar 用则可一并清; 若他处复用则保留 — 执行时核对引用。

## 验收标准
- [ ] board.js 中 `cmd-bar`/`cmd-btn`/`cmd-out`/`wireCmdBar`/`data-quick` 全部无残留 (grep 零命中)。
- [ ] 后端 `doctor` 命令仍存在且 `skein.py doctor` 可跑 (start 前置体检不受影响)。
- [ ] 前端资源无语法错误 (board.js 可被正常解析), 相关测试/门禁通过。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 任务/子任务/调度: task.json (`skein.py subtask list remove-doctor-btn`)
