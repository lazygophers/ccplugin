# workflow.md 注入 (纯增量追加, 不替换原生)

把 **强推 task** + **subtask 拆分** + **worktree 隔离** + **闭环收尾** + **task.md 看板维护** 五个维度增量注入 `.trellis/workflow.md`。trellis 原生 `inject-workflow-state` hook 每轮读这些块, 注入内容随之生效。

## 核心原则: 增量追加, 绝不替换原生

⛔ 硬规: apply 只在 workflow-state 块原生内容**之后**追加 marker。任何对原生文本的替换 / 覆盖 / 重写 = 流程错误, 不得提交。

- ✅ 注入: `[workflow-state:no_task]` 加**强推 task** / `[workflow-state:planning]` 加 subtask 拆分 + task.md 看板更新 / `[workflow-state:in_progress]` 加 worktree 隔离 + 闭环收尾 + task.md 看板维护
- ❌ **禁替换**: 任何块的原生文本 (尤其 no_task 的「分类 + 征得同意」、Phase 流程、完成判定、前缀) 一字不改
- 注入方式: 全部 marker 插在块**原生内容之后**, 原生行原样保留

> 教训: 早期版本**重写** no_task + Phase 流程, 导致 trellis 原生 task 创建不再触发。根因是替换原生文本, 不是追加本身。修正: no_task 可末尾追加倾向 marker, 但 MUST 保留原生「First classify... ask for task-creation consent」文本 (验证段强制断言)。

### 失败处理: 原生文本疑被破坏

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 验证段报「原生正文 <40 字符」 | 从 git stash / `git checkout .trellis/workflow.md` 恢复原生, 重跑注入只追加不替换 | `git stash pop` 回滚全部 apply 变更, 0 改动退出并报告用户 |
| workflow-state 标签起止数不配对 | 定位串位 marker, 删除重注 (按下方注入算法重跑) | 同上回滚, 报「注入破坏标签结构」 |
| task.py current 注入后报错 | diff 对比注入前后, 撤销改动只保留 marker 追加 | 同上回滚, 报「注入破坏 trellis 解析」 |

## i18n: 整个 workflow.md 用设备语言 (含翻译原生)

apply 完成后整个 workflow.md 的**叙述文本**必须 = 设备语言, 不只 trellisx 注入部分。

**步骤 2.5 全文档翻译** (workflow 主语言 ≠ 设备语言时):
1. 检测 workflow.md 现有叙述主语言 (trellis init 默认英文)
2. 若 ≠ 目标语言 (如设备中文) → 逐段翻译 workflow.md 的**叙述/说明文本**为目标语言
3. **保留原样不译** (机器标识, 译了 trellis 解析会坏):
   - workflow-state 标签 `[workflow-state:no_task]` `[/workflow-state:planning]` 等
   - trellisx marker `<!-- trellisx:start:X -->` `<!-- trellisx:end:X -->`
   - `task.py create/start/...` 命令 + 参数
   - 文件路径 (.trellis/tasks/... / .worktrees/...)
   - 代码块 (```bash ```python ```) 内容
   - frontmatter key / 平台名 (Claude Code / Codex...)
4. trellisx 注入 snippet 本身也用目标语言写

> 注: 翻译会改 trellis 原生 workflow 文本。`trellis update` 用英文模板覆盖后, 重跑 apply 恢复翻译。这是 trellis 模板机制的固有取舍。

## 清理无效内容 (步骤 2.5 一并做)

trellis workflow.md 含大量**模板内部说明注释** (给维护者看, 对 AI 执行无价值, 占 context), 如:
```
<!-- Per-turn breadcrumb: shown while status='in_progress' when codex.dispatch_mode=inline. ... -->
<!-- Codex-only opt-in alternate to [workflow-state:in_progress]. ... -->
```

apply 优化时移除这些无效注释:

```python
# 移除所有 HTML 注释, 但保留 trellisx 功能 marker
import re
s = read(".trellis/workflow.md")
def keep(m):
    return m.group(0) if "trellisx:start:" in m.group(0) or "trellisx:end:" in m.group(0) else ""
s = re.sub(r"<!--.*?-->", keep, s, flags=re.DOTALL)
# 清理移除后留下的多余空行 (连续 >2 空行压成 1)
s = re.sub(r"\n{3,}", "\n\n", s)
write(".trellis/workflow.md", s)
```

**保留**: `<!-- trellisx:start:X -->` / `<!-- trellisx:end:X -->` (功能 marker)。
**移除**: 其余所有 `<!-- ... -->` (trellis 模板说明)。

### ② 收敛跨平台枚举清单

trellis workflow 为多平台通用, 含大量平台名罗列, 对单平台 (Claude Code) 用户是噪音, 占 context:
```
- 1.3 Configure context — Claude Code, Cursor, OpenCode, Codex, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi
Sub-agent dispatch protocol applies to all platforms ... class-2 Codex/Copilot/Gemini/Qoder ...
```

apply 把这类**多平台枚举收敛为当前平台**:
- `[Claude Code, Cursor, OpenCode, codex-sub-agent, Kiro, Gemini, Qoder, CodeBuddy, Copilot, Droid, Pi]` → `Claude Code`
- "applies to all platforms, including class-2 Codex/Copilot/Gemini/Qoder" → 删跨平台限定, 仅留 Claude Code sub-agent 规则
- 仅 Claude Code 相关的 hook / skill / agent 名保留; 其他平台专属名 (Cursor/Codex/Kiro 等) 删

> 判定: 名字不是 Claude Code 生态 (Claude Code / sub-agent / Task / skill / hook) 的平台枚举 = 噪音, 收敛掉。保留 trellis 通用机制名 (task.py / workflow-state / Phase)。

> 注: 同 i18n 翻译, 清理改 trellis 原生 workflow。trellis update 还原后重跑 apply。

## 注入机制 (marker 幂等)

```
<!-- trellisx:start:<key> -->
<内容>
<!-- trellisx:end:<key> -->
```
重复跑: 同 key marker → 替换内容; 无 → 在锚点块**末尾**追加 (原生内容之后)。

## 注入点 0: `[workflow-state:no_task]` 块末尾追加强推 task

**愿景: 除极简任务外一律走 Trellis task; 不确定就问用户。** 在 no_task 原生「分类 + 征得同意」之后追加, 不替换原生 (原生仍先分类、仍征得同意)。把"可建可不建"调为"默认建, 除非极简"。

```
<!-- trellisx:start:no_task -->
trellisx 规约 (强化上方原生判定, 不替换): 本项目愿景 = 除极简任务外, 一律走 Trellis task 执行。
- 涉及代码改动 / 多步骤 / 跨文件 的请求 → **默认创建 task** (不是"倾向建", 是默认就建; 仅用户明确拒绝才 inline)。建议直接用 AskUserQuestion 征得同意并进入 planning, 而非自行 inline。
- 边界模糊 (拿不准该不该建, 或 simple 还是 complex) → **MUST 主动用 AskUserQuestion 问用户** "本轮是否创建 Trellis task?", 禁默认跳过 / 禁自行替用户决定。
- 仅极简任务 (纯问答 / 查询 / 单行琐改 / 纯解释说明) 可不建。
- 判断"新建 task"还是"并入现有 task"时, 读 `.trellis/task.md` 看板对照现有任务 (id/名称/描述/状态) 辅助判断。
原生的「先分类 + 征得同意才建」不变 — 但默认倾向从"可建可不建"上调为"默认建, 除非极简或用户拒绝"。
<!-- trellisx:end:no_task -->
```

## 注入点 1: `[workflow-state:planning]` 块末尾追加 subtask

**判定标准 = trellis 原生 parent/child 语义, 不看数量。** 启用拆分的开关是「本请求是否含**多个独立可验收交付** (independently verifiable deliverables)」—— 与 trellis workflow.md 原生 parent/child 判据一致, 不再用「subtask 数量 ≥2」一刀切。

```
<!-- trellisx:start:planning -->
trellisx 规划规约 (启用判定跟随 trellis 原生 parent/child 语义, 不看数量):

判定: 本请求是否含**多个独立可验收交付** (各自可独立 plan/implement/check/archive)?
- **是 (多交付)** → 拆为 parent + child tasks (trellis 原生 `task.py create --parent`)。每个 child 独立 worktree; 无依赖的 child MUST 并行执行 (同一回复一次性派多 agent)。PRD MUST 含 mermaid 调度图显式标并行组 + 依赖箭头。child 间依赖写进 child 自己的 prd.md/implement.md (非树位置隐含)。
- **否 (单一交付)** → 轻量单 task inline, **不强制拆 subtask**。仍走单 worktree 隔离。

拆分目的 = 让独立可验收交付各自隔离 + 最大化并行, 缩短关键路径; 不是为凑数量。详见 trellisx-orchestrate skill。

task 创建后, 用 `trellisx-workspace` 及时更新 `.trellis/task.md` 看板表 (新增/更新该任务行)。
<!-- trellisx:end:planning -->
```

## 注入点 2: `[workflow-state:in_progress]` 块末尾追加 worktree

```
<!-- trellisx:start:in_progress -->
⛔ trellisx 执行硬规 (本 task 必守, 违反即流程错误):

1. **强制 worktree** (两种模式都守): 本 task 全部源码改动 MUST 落在 worktree (git 根/子仓 .worktrees/<worktree>, trellis 生命周期 hook 已自动建)。**禁在主工作区写源码** — 写盘 file_path 必须是 worktree 路径。
2. **多交付并行模式** (本请求拆了 parent + child tasks): 每个 child MUST 派 sub-agent (isolation:worktree) 或 agent-team 成员执行, **main 禁直接写源码** (只拆分/派发/收集/合并/协调)。无依赖的 child MUST 在同一条回复里一次性发起多个 agent 调用 (真并行), 禁逐个串行派。严格按 PRD 调度图依赖 + 并行组执行, 禁跳步。
3. **单一交付轻量模式** (单 task 未拆 child): main 可在 worktree 内直接 edit 实施, 无需派 agent。仍守第 1 条 (写盘路径在 worktree)。
4. **强制闭环收尾 (check 通过后跑 `trellisx-finish.py`, 不停在「提醒」)**: `trellis-check` 通过后, AI **强制调用** `python3 .trellis/scripts/trellisx-finish.py [--message "<提交消息>"]` 一键收尾, 不把收尾降级为"提醒用户运行 /finish-work" —— **finish 与 worktree 删除是必须的, 非可选**。脚本按序自动执行 (失败任一步非 0 退出, 停下不静默继续):
   ① **worktree 内提交** —— `git add -A` + `git commit` (消息由 AI 经 `--message` 传入, 缺省 `chore(task): <tid> 收尾提交`), 落到 `trellisx-<name>` 分支。
   ② **合并回主分支** —— `git merge --no-ff trellisx-<name>`; **合并冲突 → 脚本自动 `merge --abort` + 报冲突文件清单 + 非 0 退出**, AI 停下转手动, 禁强解。**未合并就 archive = 分支被销毁丢提交** (见 `trellisx-worktree.py` 教训, 故脚本先合并)。
   ③ **archive** —— `task.py archive <tid>` 归档 + 触发 hook 销毁**已合并**的 worktree + 删分支。
   - **commit 强制 (owner 授权)**: 本项目 owner 已显式要求 trellisx 流程**强制提交收尾**, 脚本直接 commit 不再逐次等用户确认。AI 调用前用一行展示提交意图 (消息 + 文件范围), 但不阻塞等待。此为 owner 对自有注入流程的设计授权, 覆盖默认「禁主动 commit」。
   - **check 未过** → 修复重检, 禁跑 finish 脚本; **未 archive = 流程未闭环, 禁宣告 Done / 禁结束本轮**。
   - 会话 journal 按需: 脚本不含 journal, 需要记录会话则收尾后另跑 `/trellis:finish-work` (可选)。
5. **及时维护 task.md 看板**: start / 阶段推进 (exec→check→finish) / archive 后, MUST 用 `trellisx-workspace` 更新 `.trellis/task.md` 看板行 (状态/阶段/进度/worktree)。看板滞后于实际 = 流程缺陷。
6. 收每个 agent 返回立即回传用户进度; task archive 时 worktree 干净则自动销毁。
7. **任务中途修正路由 (执行中收到用户新指令)**: 本 task 已在跑 (agent/member 已派发) 时收到新指令, coordinator 先判归属:
   - **属当前任务** (修正 / 补充 / 细化已派交付) → ⛔ 禁 main 自己直接改源码、禁开新 task。按序: ① 先改对应**真值文档** (`prd.md` / `design.md` / `implement.md` 受影响条款, 标锚点) → ② 对**仍在跑**的目标 agent/member 用 `SendMessage` 下发修正 (引用改后 PRD 锚点, 令其就地纠偏, 不等跑完返工)。**先改文档再通知** (PRD 是真值, agent 复读以对齐)。
   - **独立新任务** (与当前交付无关) → 走 no_task 强推 task (新建 / 排队), 不打断当前 agent。
   - **判不准** → 🔴 用 AskUserQuestion 让用户裁定「并入当前任务 / 另起新任务」, 禁擅自二选一。
   兜底: 目标 agent 已完成 / workflow 模式无法中途 SendMessage → 改在 check 阶段按新 PRD 纠正, 或停掉重派一个修正 agent; inline 单交付 (无 running agent) → main 改 PRD 后就地调整执行, 跳过 SendMessage。
<!-- trellisx:end:in_progress -->
```

## 注入点 3: `[workflow-state:in_progress-inline]` 块末尾 (codex inline)

```
<!-- trellisx:start:in_progress_inline -->
trellisx (增量): inline 模式 main 直接 edit, 但源码目标路径必须在 worktree (.worktrees/<worktree>) 内。
<!-- trellisx:end:in_progress_inline -->
```

## 注入点 4: finish 段强制化 (⚠️ 局部豁免铁律1 — 用户授权)

> **此注入点是铁律1「绝不替换原生」的唯一例外**, 仅限 Phase 3 的**收尾提醒段** (原生 "3.5 收尾提醒" / 含 `/finish-work` 提醒的段落)。用户已显式授权 apply **改写** finish 段, 把「提醒用户可运行 /finish-work」升级为「强制跑 `trellisx-finish.py`」。其余原生段 (no_task 分类/同意、planning、check、回复前缀) 仍**一字不动**。

定位原生收尾提醒段 (含 `finish-work` 的 `#### 3.x` 段), 用 marker 包裹**替换其正文** (幂等):

```
<!-- trellisx:start:finish_force -->
⛔ **强制收尾 (不是提醒)**: check 通过后, AI **必须**运行
`python3 .trellis/scripts/trellisx-finish.py [--message "<提交消息>"]` 一键收尾
(提交 worktree → 合并回主分支 → archive → 销毁 worktree)。
**finish 与 worktree 删除是必须的, 非可选, 非「提醒用户去做」。**
- 合并冲突 → 脚本 abort + 报冲突 + 非 0 退出 → 转手动, 禁强解。
- check 未过禁跑脚本; 未 archive = 流程未闭环, 禁宣告 Done。
- commit 为 owner 授权的强制动作 (脚本直接提交); 需会话 journal 另跑 `/trellis:finish-work`。
<!-- trellisx:end:finish_force -->
```

注入算法 (定位 + 幂等替换, 失败兜底):

```python
s = read(".trellis/workflow.md")
START, END = "<!-- trellisx:start:finish_force -->", "<!-- trellisx:end:finish_force -->"
block = f"{START}\n{finish_force_snippet}\n{END}"
if START in s:                                   # 已注入 → 替换 marker 内
    s = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block, s, flags=re.DOTALL)
else:
    # 定位原生收尾段: 含 finish-work 的 #### 标题段 (i18n 无关, 匹配命令字串)
    m = re.search(r"(####[^\n]*\n(?:(?!\n####).)*?/?(?:trellis:)?finish-work(?:(?!\n####).)*)",
                  s, re.DOTALL)
    if m:                                        # 用 marker 块取代该段正文 (保留标题行)
        title = m.group(1).split("\n", 1)[0]
        s = s[:m.start(1)] + f"{title}\n\n{block}\n" + s[m.end(1):]
    # 定位不到 → 不强改 (in_progress 硬规 #4 已是权威覆盖), 跳过
write(".trellis/workflow.md", s)
```

> 兜底: 定位不到原生收尾段 (措辞被大改 / 已 i18n 到无 `finish-work` 字串) → **跳过本注入点**, 不强行改写。此时 in_progress 块硬规 #4 (强制跑 `trellisx-finish.py`) 已是权威覆盖, finish 行为仍强制。

## 注入点 5: 复制 `trellisx-finish.py` + `trellisx_wt.py` 公共模块

apply 执行时把插件 `scripts/trellisx-finish.py` **及其依赖** `scripts/trellisx_wt.py` 复制到目标项目 `.trellis/scripts/` (与 `trellisx-worktree.py` / `trellisx-taskmd.py` 同目录, 见 `hook-injection.md`)。`chmod +x` 脚本。`trellisx_wt.py` 是 worktree 路径/分支/命名单一真值, `trellisx-finish.py` 与 `trellisx-worktree.py` 都 `import trellisx_wt` —— **漏拷它两脚本 ImportError**。

## 注入算法

```python
content = read(".trellis/workflow.md")
INJECT = {  # 末尾追加, 绝不替换原生; no_task 仅加倾向不动原生分类/同意
    "no_task": no_task_snippet,
    "planning": planning_snippet,
    "in_progress": in_progress_snippet,
    "in_progress-inline": in_progress_inline_snippet,
}
for tag, snippet in INJECT.items():
    key = tag.replace("-", "_")
    start, end = f"<!-- trellisx:start:{key} -->", f"<!-- trellisx:end:{key} -->"
    if start in content:                          # 已注入 -> 替换 marker 内
        content = re.sub(f"{start}.*?{end}", f"{start}\n{snippet}\n{end}", content, flags=re.DOTALL)
    else:                                          # 未注入 -> 在该 workflow-state 块原生内容之后插入
        m = re.search(rf"(\[workflow-state:{tag}\].*?)(\n\[/workflow-state:{tag}\])", content, re.DOTALL)
        if m:
            content = content[:m.end(1)] + f"\n{start}\n{snippet}\n{end}" + content[m.end(1):]
        # 块不存在 -> 跳过 (不强行创建, 不破坏原生)
write(".trellis/workflow.md", content)
```

## 验证 (确保没破坏原生)

```bash
# 原生 workflow-state 标签配对 (起始 = 结束数)
grep -c "\[workflow-state:" .trellis/workflow.md
grep -c "\[/workflow-state:" .trellis/workflow.md
# ★ 关键: no_task 原生内容仍在 (注入只追加没替换 — 规避踩坑根因)。
# 语言无关 (i18n 翻译后原生变中文, 不能死匹配英文串): 检 no_task 块除 trellisx marker 外原生正文非空
python3 - <<'EOF'
import re
s=open(".trellis/workflow.md").read()
m=re.search(r"\[workflow-state:no_task\](.*?)\[/workflow-state:no_task\]", s, re.DOTALL)
body=m.group(1) if m else ""
native=re.sub(r"<!-- trellisx:start:no_task -->.*?<!-- trellisx:end:no_task -->","",body,flags=re.DOTALL).strip()
print(f"{'✓' if len(native)>40 else '✗ 危险: 原生疑被替换/清空'} no_task 原生正文 {len(native)} 字符 (除 trellisx marker)")
EOF
# task.py 创建流程未坏
python3 .trellis/scripts/task.py current >/dev/null 2>&1 && echo "task.py OK"
```

🔴 CHECKPOINT — 上述 no_task 原生正文断言出 ✗, 立即停止后续步骤, 走「失败处理: 原生文本疑被破坏」表回滚, 禁带病继续写盘。

## 不破坏 trellis 原生

- 全部 marker 只在块**末尾追加**, 原生行一字不改 (含 no_task)
- no_task 注入仅加**强推 task 规约**, **MUST 保留原生**「分类 + 征得同意」语义内容 (上方验证以语言无关方式断言原生正文非空; i18n 翻译可改其语言, 但不可清空/替换)
- workflow.md 被 trellis update 覆盖后, 重跑 apply 恢复注入 (幂等)
