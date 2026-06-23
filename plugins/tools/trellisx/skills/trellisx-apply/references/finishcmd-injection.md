# plan-finishcmd / write-finishcmd: 目标 finish-work 命令全链注入 (Option B)

apply 往**目标项目**的 `.claude/commands/trellis/finish-work.md` 注入一步, 让 `/trellis:finish-work` 自己就做**全链收尾** (commit→merge→del worktree→archive→finish→journal), 与 after_finish hook 路殊途同归。

## 为什么必须注入 (修原生缺陷)

trellis 原生 `/trellis:finish-work` 跑 `task.py archive <tid>` **直接归档** —— 它 **不跑 `task.py finish`**, 所以 **after_finish hook 的 commit+merge 链被绕过**。后果:
- 不提交 worktree 内代码、不合并 worktree 分支回主分支;
- `task.py archive` 触发 `after_archive` 直接销毁 worktree → **未合并就销 = 丢 worktree 内提交** (正是 `trellisx-worktree.py` 的教训)。

故 apply MUST 改造目标 finish-work, 让它**先跑全链再 journal**。

## 注入物: `.claude/commands/trellis/finish-work.md` (marker 幂等)

在原生 finish-work 的 **archive 步骤之前** (原生 "Step 3: Archive" / 含 `task.py archive` 的步骤前) 插入 marker 块:

```
<!-- trellisx:start:finishcmd_fullchain -->
⛔ **trellisx 全链收尾 (在原生 archive/journal 之前先跑)**: 本项目 worktree 隔离, 收尾 MUST 先合并再归档, 否则销毁 worktree 丢提交。

⓪ **AI 层 — 先确认本 task 的 Workflow / 后台任务已终止 (脚本做不到, 必须 AI 主动)**: 跑收尾脚本前, 用 `TaskList` 查有无悬挂的后台 Workflow/agent 任务 (本 task 的 exec/check 载体 —— **Claude Code Workflow** 或退化的**其他平台 agent 流水线**); 有残留则 `TaskStop` 逐个关闭, 再跑脚本。**`trellisx-finish.py` 只销 worktree, 不关 Workflow/Task** —— 关闭悬挂任务是 AI 层职责, 脚本不代劳。悬挂任务未清就合并/销毁 worktree = 进程仍在写 = 流程错误。

**git 层 — 跑 `python3 .trellis/scripts/trellisx-finish.py`** (确定性脚本):
① worktree 内 `git add -A` + commit (落 `trellisx-<name>` 分支)
② `git merge --no-ff trellisx-<name>` 合并回主分支, 子先主后 (冲突 → abort + 报冲突 + 非 0 退出, 转手动禁强解)
③ `task.py archive <tid>` 归档 + 触发 after_archive 销毁**已合并**的 worktree

跑完后**跳过下方原生 "Step 3: Archive"** (trellisx-finish.py 已 archive), 直接进原生 journal 步骤 (add_session.py)。
若 trellisx-finish.py 非 0 退出 (合并冲突) → 停, 转手动, 禁继续 journal/宣告 Done。
<!-- trellisx:end:finishcmd_fullchain -->
```

> 与 hook 路的关系: `task.py finish` 走 after_finish hook 做全链; `/trellis:finish-work` 走本注入做全链。**两路都做全链, 二选一即可**, 不重复 (finish-work 注入跑的是 archive 不是 finish, 不触发 after_finish; hook 路不经 finish-work)。i18n: 注入文本用目标语言。

## 注入算法 (定位 + 幂等)

```python
import re, os
target = ".claude/commands/trellis/finish-work.md"
if not os.path.isfile(target):
    pass   # 目标无 finish-work 命令 → 跳过 (hook 路仍保证全链), 报告未注入
else:
    s = open(target, encoding="utf-8").read()
    START, END = "<!-- trellisx:start:finishcmd_fullchain -->", "<!-- trellisx:end:finishcmd_fullchain -->"
    block = f"{START}\n{fullchain_snippet}\n{END}"
    if START in s:                                  # 已注入 → 替换 marker 内 (幂等)
        s = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, s, flags=re.DOTALL)
    else:
        # 在原生 archive 步骤前插入: 定位含 `task.py archive` 的标题段, 在其标题行前插
        m = re.search(r"(?m)^#+[^\n]*\n(?:(?!\n#).)*?task\.py archive", s, re.DOTALL)
        if m:
            ins = m.start()
            s = s[:ins] + block + "\n\n" + s[ins:]
        else:
            s = s.rstrip() + "\n\n" + block + "\n"   # 定位不到 → 追加末尾 (兜底, hook 路仍兜)
    open(target, "w", encoding="utf-8").write(s)
```

> ⚠️ 这是 apply **对目标项目文件**的修改 (apply 运行时行为), 不是改 trellisx-apply skill 自身。`write-finishcmd` 独占 `.claude/commands/trellis/finish-work.md`, 不与其他 writer 重叠。

## 边界

- 目标无该文件 → 跳过 + 报告 (hook 路 `after_finish` 仍保证全链, 不致命)。
- 原生 finish-work 措辞被大改 / 定位不到 archive 步骤 → 追加到末尾兜底。
- 只加 marker 块, **不删/不改**原生 journal / archive 步骤正文 (跳过逻辑写在 marker 内由 AI 执行)。

## 验证 (verify-finishcmd)

```bash
F=.claude/commands/trellis/finish-work.md
[ -f "$F" ] || { echo "(无 finish-work.md, 跳过 — hook 路兜底)"; exit 0; }
grep -q "trellisx:start:finishcmd_fullchain" "$F" && echo "✓ finish-work 含全链注入" || echo "✗ finish-work 未注入全链"
grep -q "trellisx-finish.py" "$F" && echo "✓ 引用 trellisx-finish.py 全链" || echo "✗ 缺全链脚本调用"
```
