# 移除新建 task 按钮 — 详细设计

## 改动 (单文件 board.js)

### 1. CSS (L159-165) 删
- `.cmd-new` + `.cmd-new:hover` (L159-160) — 新建按钮专属
- `.cmd-form` + `.cmd-form[hidden]` + `.cmd-form .f` + `.cmd-form .f>span` + `.cmd-form .f>input,.cmd-form .f>textarea` (L161-165) — 表单专属

保留: `.cmd-bar` / `.cmd-spacer` / `.cmd-btn` / `.cmd-out` (doctor + 结果区用)

### 2. wireCmdBar (L497-555) 改
- `var form = mount.querySelector('[data-form="create"]');` → 删 (表单不在)
- toggle-new / cancel-new 分支 (L539-540) → 删
- form submit create 逻辑 (L545-554) → 删
- `if (cmd === "create" && ...)` 重置块 (L528-533) → 删 (create 不再从表单触发)
- 保留: doctor / run / renderResult / bar click (quick 分支)

### 3. render() HTML 模板 (L564-578) 改
删:
```
'<button ... class="cmd-btn cmd-new" data-cmd="toggle-new">＋ 新建 task</button>'
'<span class="cmd-spacer"></span>'   ← 若 doctor 不需 spacer 也可删, 保留无害
'<form class="cmd-form" hidden data-form="create"> ... </form>'
```

保留:
```
<div class="cmd-bar">
  <button ... data-quick="doctor">doctor</button>
</div>
<div class="cmd-out" hidden data-out></div>
```

cmd-spacer 原顶按钮右推用, 删新建按钮后 doctor 独占左侧, spacer 无意义 → 删。

## 取舍

- **不删 wireCmdBar 整体**: doctor 仍用 run()/renderResult()/cmd-out。只删新建相关分支。
- **form 变量清理**: wireCmdBar 内 `var form` 及所有 form.* 引用随表单删一并清, 防 null ref。
- **create 命令本身保留 (api.exec)**: run() 通用, 未来其他快捷按钮可能用; 只删触发 create 的表单入口。

## 不含调度图

单文件微改 (board.js ~30 行删 + 模板改), worktree 豁免原地做。
