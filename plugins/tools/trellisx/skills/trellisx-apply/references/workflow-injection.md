# workflow.md 注入 (纯增量追加, 不替换原生)

把 **强推 task** + **subtask 拆分** + **worktree 隔离** + **闭环收尾** + **task.md 看板维护** 五个维度增量注入 `.trellis/workflow.md`。trellis 原生 `inject-workflow-state` hook 每轮读这些块, 注入内容随之生效。

## 核心原则: 增量追加, 绝不替换原生

**apply 只在 workflow-state 块原生内容之后追加 marker, 绝不替换 / 覆盖 / 重写原生文本。**

- ✅ 注入: `[workflow-state:no_task]` 加**强推 task** / `[workflow-state:planning]` 加 subtask 拆分 + task.md 看板更新 / `[workflow-state:in_progress]` 加 worktree 隔离 + 闭环收尾 + task.md 看板维护
- ❌ **禁替换**: 任何块的原生文本 (尤其 no_task 的「分类 + 征得同意」、Phase 流程、完成判定、前缀) 一字不改
- 注入方式: 全部 marker 插在块**原生内容之后**, 原生行原样保留

> 教训: 早期版本**重写** no_task + Phase 流程, 导致 trellis 原生 task 创建不再触发。根因是替换原生文本, 不是追加本身。修正: no_task 可末尾追加倾向 marker, 但 MUST 保留原生「First classify... ask for task-creation consent」文本 (验证段强制断言)。

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
4. **强制闭环 (plan→exec→check→finish)**: 实施完成后 MUST 走完整闭环 —— `trellis-check` 质量验证 → 通过后提交 (Phase 3.4) → `task.py archive` 归档收尾。**check 未过 → 修复重检, 禁跳到 finish; 未 archive = 流程未闭环, 禁宣告 Done / 禁结束本轮**。不要做完 check 就停在 in_progress, 必须主动推进到 archive。
5. **及时维护 task.md 看板**: start / 阶段推进 (exec→check→finish) / archive 后, MUST 用 `trellisx-workspace` 更新 `.trellis/task.md` 看板行 (状态/阶段/进度/worktree)。看板滞后于实际 = 流程缺陷。
6. 收每个 agent 返回立即回传用户进度; task archive 时 worktree 干净则自动销毁。
<!-- trellisx:end:in_progress -->
```

## 注入点 3: `[workflow-state:in_progress-inline]` 块末尾 (codex inline)

```
<!-- trellisx:start:in_progress_inline -->
trellisx (增量): inline 模式 main 直接 edit, 但源码目标路径必须在 worktree (.worktrees/<worktree>) 内。
<!-- trellisx:end:in_progress_inline -->
```

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

## 不破坏 trellis 原生

- 全部 marker 只在块**末尾追加**, 原生行一字不改 (含 no_task)
- no_task 注入仅加**强推 task 规约**, **MUST 保留原生**「分类 + 征得同意」语义内容 (上方验证以语言无关方式断言原生正文非空; i18n 翻译可改其语言, 但不可清空/替换)
- workflow.md 被 trellis update 覆盖后, 重跑 apply 恢复注入 (幂等)
