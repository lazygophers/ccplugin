# task详情PRD章节化为tab/todo + prd.md fmt规范化hook — 详细设计

架构 / 数据流 / 关键取舍 (调度归 task.json):

## 三块改动 (独立文件, 低耦合)
| 块 | 文件 | 依赖 |
|----|------|------|
| FE 章节化 | webapp/src/pages/task.js (仅 PRD tab) | 无 (独立) |
| fmt CLI | skein.py (add_parser + dispatch + MUTATING + `def fmt`) | 无 (独立文件) |
| fmt hook | plugin.json (PostToolUse) + hooks.py (cmd_fmt) | fmt CLI (hook 调 `skein fmt`) |

## 数据流
- **FE**: 前端拿 docs.prd 原文 → `^##\s+(标题)` 正则分节 → 每节内一级 `- [ ]`/`- [x]` 提勾选态 → card/accordion 竖排渲染 (todo 只读)。非 checkbox 内容 (prose/子 list) 按普通 md 渲染在 card 内。零后端改动。
- **fmt**: `skein fmt <id>` 读 prd.md → 解析章节 → 各章节一级 `-` list 项补成 `- [ ]` (已 checkbox 保勾选态) + 章节顺序/标题校验 → 不规范抛错非零退出 → 规范则写回 (幂等)。
- **hook**: 写 prd.md (Edit/Write/MultiEdit) → PostToolUse → hooks.py cmd_fmt 判 file_path 匹配 `.skein/task/*/prd.md` → 提 task-id → 调 `skein fmt <id>`。防循环: fmt 内容无变化不写 / 或 hook 只对用户/AI 写触发, fmt 自身写回不经此 hook (PostToolUse 只匹配工具调用, python 直接写文件不触发, 天然不循环)。

## 关键取舍
- **前端解析 vs 后端 prd_data**: 走前端 (§recon 岔口4)。prd_data 仅覆盖 2/4 章节且 board 专用, 前端 `## ` 分节 ~15 行覆盖全四章节, 零后端改动、不动 docs 契约。
- **fmt 两入口** (CLI + hook, §recon 岔口1 用户选 c): CLI 实现全部逻辑, hook 仅薄封装调 CLI, 不重复逻辑。
- **todo 只读** (§recon 岔口3 用户选 a): 复用勾选态解析, 不回写, 避与 "TODO 未勾清=未收敛" planning 语义冲突。
- **card 竖排** (§recon 岔口2 用户选 a): 复用旧 board prdBlock 视觉, 新代码少。
- **顶层条件指令规避**: 章节列表/空态/todo 态条件禁放页面模板顶层 (petite-vue 崩溃坑), 下沉内层容器。
- **防 hook 循环**: PostToolUse 只对 Claude 工具写 (Edit/Write) 触发; skein fmt 用 python 文件 IO 写回, 不经工具层 → 不自触发, 无循环。
