# 调研: task 详情页 PRD 章节化 tab/todo + prd.md fmt 规范化 hook (代码勘察)

范围: 只读 plugins/tools/skein/。task-id=task-prd-tabs-fmt。

## 1. task.js 现状 (PRD 如何渲染)
文件 plugins/tools/skein/assets/webapp/src/pages/task.js
- 三文档 tab 静态定义: `DOC_TABS = [{key:"prd",label:"PRD"},{key:"design",label:"详细设计"},{key:"findings",label:"调研收敛"}]` (task.js:106-110)
- 单层 tab 切换, `tab` 默认 "prd" (task.js:134); tab bar 渲染 docTabs, 空文档标"空" (task.js:44-52)
- 内容区: 整块 markdown 渲染, 无章节拆分 —— `<div class="md-body" v-html="renderedDoc">` (task.js:57)
- renderedDoc = `md.renderSafe(this.docs[this.tab] || "")` (task.js:141); 即拿后端返回的整篇 md 原文一次性渲染
- 数据来源: `api.task(params.id)` 返回 `{task, docs, subtasks, contracts, archived}`, docs = {prd, design, findings} 原文字符串 (task.js:118-121)
- docLabel(k) 取 tab 标签 (task.js:140)
- 软刷 onLive 整体重挂 mountApp, 会丢当前 tab 选择 (task.js:146-147)
结论: 当前 PRD 是"整篇 md v-html", 无章节 tab, 无 todo 交互。要章节化需在前端解析 md 分节 (## 标题) 或改用后端已有的 prd_data 结构化解析 (见 §2/§5)。

## 2. PRD 内容结构约定 (章节 + markdown 结构)
生成源 = python 脚手架, 非 skill 手写:
- plugins/tools/skein/scripts/skein.py:347-371 `_scaffold()` 落 prd.md 骨架, 模板固定四章节 (`## 标题`):
  - `## 目标` (355)
  - `## 边界` (356)
  - `## 验收标准` (357)
  - `## 索引` (358) — 链 design.md/findings.md/task.json
  每章节自带 `- [ ] TODO: ...` 占位 checkbox
- skill 侧一致约定: skein-plan/SKILL.md:59 "prd.md (主入口) — 分章节: **目标 / 边界 / 验收标准 / 索引**。每章节自带 `- [ ] TODO`, 填完逐个勾掉; 未勾清 = planning 未收敛"
结论: PRD 标准章节 = 目标 / 边界 / 验收标准 / 索引, markdown 结构用 `## 二级标题` + `- [ ]`/`- [x]` checkbox list + 普通 `-` list。章节标题是稳定锚点, 可据 `^##\s+(标题)` 分节。

## 3. python CLI 命令入口 (子命令注册 + fmt 现状)
plugins/tools/skein/scripts/skein.py
- argparse: `p = ArgumentParser` (2257); `sub = p.add_subparsers(dest="cmd", required=True)` (2264)
- 各子命令 `sub.add_parser("init"/"create"/"start"/"finish"/"subtask"/"serve"/"view"/"doctor"/...)` (2266-2308)
- dispatch 表: `dispatch = {"init":sk.init, "create":sk.create, ... "subtask":sk.subtask}` (2351-2358)
- 写命令加工作区锁: `MUTATING = {...}` (2361-2362); 会改文件的命令须列入
- 现有 fmt: **无 `skein fmt` 子命令**。grep "fmt" 命中的都是内部 helper (_yaml_dump 的 fmt / _fmt_ts / fmt_dur) 与注释里提到用户项目自带的 rust-fmt.py (skein.py:2012,2096), 均非 prd 格式化。搜词: fmt/format/prettier/normalize。
结论: 新增 `skein fmt <id>` 挂点 = ① 加 `sub.add_parser("fmt", ...)` 于 2308 附近 ② dispatch 加 `"fmt": sk.fmt` (2357) ③ 若改写 prd.md 须把 "fmt" 加进 MUTATING (2361) 上锁 ④ 实现 `def fmt(self, a)` 方法。

## 4. 现有 hook 基础设施 (能否 prd.md 写入触发)
配置在 plugins/tools/skein/.claude-plugin/plugin.json:73-171 (非 settings.json —— .claude/settings.json 只有 enabledPlugins 开关)
已接线 hook:
- SessionStart: skein-memory session-start / skein session-context / pip install (76-)
- UserPromptSubmit: skein user-prompt
- SubagentStart: skein-memory subagent-start
- PreToolUse matcher `Edit|Write|MultiEdit|Read` → `skein-hooks guard` (117-)
- PermissionRequest / PermissionDenied matcher Bash|Edit|Write|Read → skein-hooks permission
- PostToolBatch → skein-hooks batch
- PostToolUseFailure matcher Bash → skein-hooks report
hook 实现 plugins/tools/skein/scripts/hooks.py, dispatch = {permission, guard, batch, report} (138)。
关键: **无 PostToolUse (写后) hook**。guard 是 PreToolUse (写前拦截), 且只硬阻 BLOCKED={task.json,task.md} (hooks.py:17,77) —— prd.md **不在 BLOCKED**, AI 直接 Edit/Write prd.md 是放行的。
结论: prd.md 写入当前无任何 post 触发。要"写 prd.md 后自动 fmt"需**新增 PostToolUse hook**: plugin.json 加 `"PostToolUse": [{matcher:"Edit|Write|MultiEdit", hooks:[skein-hooks fmt]}]` + hooks.py 加 `cmd_fmt` 分派 (判 file_path 是否 .skein/task/*/prd.md, 是则调 skein fmt)。注意: PostToolUse hook 无法阻止已写入, 只能写后修正 (再改文件); 幂等 fmt 可接受。

## 5. prd.md 如何被 serve/读 (喂前端)
plugins/tools/skein/scripts/skein.py + api.js
- 前端 api: `task = (tid) => getJSON("/__skein__/task/"+tid)` (api.js:36)
- 后端 endpoint: `@app.get("/__skein__/task/{tid}")` → `board._task_detail(tid)`, 404 若不存在 (skein.py:1936-1939)
- `_task_detail` (skein.py:1532-1552): 读 task.json 全文 + 循环读 prd.md/design.md/findings.md **原文字符串** 塞进 docs={prd,design,findings}, 缺失为 None; 未归档缺失回落归档目录
- 另有静态挂载 `/task` → StaticFiles(.skein/task/) (skein.py:2004), 旧 board doc.js 直接 fetch task/<id>/prd.md 原文 (webapp task.js 没走这条, 走的是 /task/{tid} json)
- **已有结构化解析器**: `prd_data(tid)` (skein.py:1347-1383) —— 只解析 `目标`/`验收标准` 两节 (1356), 提 checkbox 勾选态 (check/done) + prose, 跳 TODO 占位, 输出 `[{name,badge,items:[{kind,done,text}]}]`。这是**旧 board** (assets/board/board-render.js:266 prdBlock) 用的, webapp task.js 未复用。
结论: webapp 走 /__skein__/task/{tid} 拿 docs 原文 (纯字符串)。若要章节 tab/todo, 两条路: (A) 前端解析 docs.prd 原文分节 (纯前端, 零后端改动); (B) 后端复用/扩展 prd_data 输出结构化章节+checkbox 态, 新增/扩 endpoint 或塞进 _task_detail。prd_data 现仅覆盖目标/验收标准两节, 要全四章节需放宽 1356 的白名单。

## 规划要点 (改哪些文件 + 技术岔口)
需改文件 (按功能):
- PRD 章节化 tab/todo (前端): plugins/tools/skein/assets/webapp/src/pages/task.js (必改)
  - 可选后端: plugins/tools/skein/scripts/skein.py 的 prd_data (1347) / _task_detail (1532) — 若走后端结构化
- fmt 规范化:
  - CLI 子命令路线: skein.py add_parser (~2308) + dispatch (2357) + MUTATING (2361) + 新 fmt 方法
  - CC hook 自动触发路线: plugin.json (~117 hooks 段加 PostToolUse) + scripts/hooks.py (加 cmd_fmt 分派 + DISPATCH:138)

技术选择岔口 (交 main + 用户拍板, 不代决):
1. **fmt 触发方式**: (a) 纯 CLI `skein fmt <id>` 手动/plan 收尾调用 —— 简单, 无 hook 复杂度, 但不自动; (b) PostToolUse hook 写 prd.md 后自动 fmt —— 自动, 但 skein 现无 PostToolUse hook 需新增基础设施, 且写后再改文件有幂等/循环触发顾虑 (fmt 改文件→再触发 PostToolUse→需自识别跳过); (c) 两者都要 (CLI 实现 + hook 调 CLI)。
2. **PRD 章节渲染: tab vs card**: (a) 二级 tab (章节各一 tab, 与现三文档 tab 嵌套) ; (b) card/accordion 竖排全章节 (旧 board prdBlock 风格, 参 board-render.js:266)。旧 board 已是 card 竖排 + badge, 可复用视觉。
3. **todo 是否可交互持久化**: prd 的 `- [ ]` 现是纯展示 (renderSafe 出静态 html)。若要点击勾选持久化, 需回写 prd.md —— 但 prd.md 是 planning 真值/AI 维护, 且已有 /__skein__/spec/save 这类写 endpoint 先例 (skein.py:1954) 可仿; 但会与 "planning 未勾清=未收敛" 语义 (skein-plan:59) 冲突, 用户手工勾选是否合适存疑。默认建议只读展示 todo 态 (复用 prd_data 的 done 解析), 交互持久化需用户明确要。
4. **章节解析放前端还是后端**: 前端解析零后端改动但重复造轮子; 后端复用 prd_data 但现仅覆盖 2/4 章节需放宽白名单 (skein.py:1356)。

需要: dispatch prompt 未明确 task-id, 已据 .skein/task/ 实际目录判定为 `task-prd-tabs-fmt` 落盘, 请 main 确认。
