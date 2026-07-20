# config 设置统一 — PRD

## 目标
config-modal 设置弹窗 + 全站输入框 UI 统一, 含 5 项改动: 删 board_theme / 合并发为单 max_active / web_serve 文案 / worktree_root 条件展示 / 全站抽公共 input class。

## 边界
- 范围内: config-modal.js SCHEMA + 逻辑, skein.py CONFIG_DEFAULTS + 调度读 max_parallel 处, test_board.py, input.css, spec.js 表单
- 范围外: 其他 webapp 页 (dashboard/board/queue/task); skein.py task 级调度逻辑 (max_active 用法不变); config.yaml 已有 board_theme/max_parallel 键的存量 (config() migration 不主动删, 静默忽略)
- 约束: 用户确认全部 5 项 + 合并方式 (单一 max_active, task+subtask 共用)

## 改动清单

### A. board_theme 全删 (st1: cfg-schema-overhaul)
- skein.py L156: CONFIG_DEFAULTS 删 `"board_theme": "skein"` 行
- config-modal.js L15: SCHEMA 删 board_theme 行
- config-modal.js L19: RESTART_KEYS 去 `"board_theme"` (只留 `"worktree_root"`)
- config-modal.js L7 注释: 去 board_theme 提及
- test_board.py L133-143 (test_set_config) + L216-225 (test_post_config): board_theme 相关断言改用其他键 (如 retain_days) 或删

### B. max_parallel 合入 max_active (st1: cfg-schema-overhaul)
- skein.py L149: CONFIG_DEFAULTS 删 `"max_parallel": 2` 行
- skein.py L200: migration `for k in ("max_active", "max_parallel")` → 去 max_parallel
- skein.py 8 处读 max_parallel 改 max_active:
  - L1237 `self.config().get("max_parallel", 2)` → `self.config()["max_active"]`
  - L1255 同
  - L1287 `mp = self.config().get("max_parallel", 2)` → `self.config()["max_active"]`
  - L1376 同
  - L1424 提示文案 `"max_parallel"` → `"max_active"`
  - L2589/2610 help 文案 max_parallel → max_active
- config-modal.js SCHEMA: 删 max_parallel 行 (max_active label 改 "并发上限", hint 改 "task 与 subtask 共用并发数")
- config-modal.js L9 注释 + L217 默认值镜像: 去 max_parallel

### C. web_serve 文案 (st1: cfg-schema-overhaul)
- config-modal.js SCHEMA: web_serve label "http 服务" → "http 服务自动启用", hint "看板 http 服务总开关" → "是否自动启用"

### D. worktree_root 条件展示 (st1: cfg-schema-overhaul)
- config-modal.js FORM_TPL: worktree_root 行加 `v-if="cfg.use_worktree"` (use_worktree off 时隐藏整行)
- 注意: FORM_TPL 当前是 SCHEMA.map 静态拼, worktree_root 行需特殊处理 (加 v-if 属性)

### E. 全站抽公共 input class (st2: input-class-unify)
- input.css: 加公共 `.field` class (font/padding/border/bg/color, 同 .cfg-input 基础样式), 或直接把 .cfg-input 提为通用
- spec.js L121-170: metadata 表单 5 处 inline `style="background:var(--bg);color:var(--fg);border:1px solid var(--brd)"` 去掉, 改 `class="field"` (或 .cfg-input)
- spec.js keywords input (L175) 同步
- config-modal.js 数字框: 确认已用 .cfg-input (无需改), 如 .field 与 .cfg-input 合并则同步

## subtask 拆分
| sid | 名称 | agent | deps | 改动文件 |
|---|---|---|---|---|
| cfg-schema-overhaul | config schema 四改 (board_theme 删 + max_parallel 合 + web_serve 文案 + worktree_root 条件) | skein-executor | — | config-modal.js, skein.py, test_board.py |
| input-class-unify | 全站抽公共 input class + spec.js 去 inline style | skein-executor | — | input.css, spec.js |

两 subtask 不共享文件 (st1 碰 config-modal.js/skein.py/test_board.py; st2 碰 input.css/spec.js), 可并行。

## 验收标准
- [ ] board_theme 全栈零引用 (skein.py + config-modal.js + test_board.py)
- [ ] max_parallel 全栈零引用, subtask 调度读 max_active
- [ ] config-modal 无 max_parallel 行, max_active label "并发上限"
- [ ] web_serve label "http 服务自动启用" + hint "是否自动启用"
- [ ] use_worktree off 时 worktree_root 行隐藏
- [ ] spec.js 表单无 inline style, 用公共 class
- [ ] input.css 有公共 input class
- [ ] skein.py ast.parse 过
- [ ] config-modal.js / spec.js ESM 过 (node -c)
- [ ] test_board.py board_theme 测试改/删后 pytest 过
- [ ] dist/app.css 重建 (若 input.css 改)
- [ ] chrome 实测: 设置弹窗显示改后 schema, worktree off 隐藏 root 行

## 索引
- 任务/子任务/调度: task.json
