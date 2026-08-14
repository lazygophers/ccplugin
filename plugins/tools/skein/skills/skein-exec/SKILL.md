---
name: skein-exec
description: "SKEIN exec 执行方法论 — skein-executor agent 绑定 skill。单个 running subtask 的完整执行纪律: workdir 硬门 + worktree 改动范围判定 + 自读 subtask 详情 (不靠转述) + spec 约定佐证 + 读后写硬门 + done 前可运行验证 + JSON 回传格式。只做范围内事, 收尾仅 subtask done/fail。"
user-invocable: false
model: sonnet
effort: medium
context: fork
---

# skein-exec — exec 执行方法论

> 🔒 本 skill 是 skein-executor agent 的执行纪律单一真值源; agent .md 只留入参/回传/边界。
> 全局流程规则 (状态机/调度/优先级) 以 skein-flow/references/ 为单一真值源。

## 工作流四步

入参只给定位信息, 详细要求靠自己读。

### 1. 定工作目录 + 读详情

- **workdir 硬门** (纯事实校验, 不推断运行模式): 开工前确认 workdir 存在且可写。不满足 → 立即 `skein subtask fail <tid> <sid> --note "workdir <路径> 不存在/不可写"` 并回传, 禁先改一堆文件再失败。
- **改动范围照入参的 `worktree` 字段, 不看路径长相**: `on` → 改动只准落在 workdir 内, 主工作区不在范围; `off` → 在仓库根原地改, 无隔离。字段缺失按 `off` 处理并在回传里标注。
- 自跑 `skein subtask show <tid> <sid>` 读 desc/验收/depends_on/skills 等全部字段, 不靠 dispatch prompt 里的转述。
- 需 spec 约定佐证时先 `skein-spec recall <关键词>` (namespace×inclusion 记忆库, 只读)。
- 缺信息 (验收模糊/依赖不明) → needs 标 `需要: <问题>`, 不猜, 不直接问用户。
- **你被派时 subtask 已是 running 态 (main 用 `skein claim` / `skein flow run` 前置占槽), 不重复占槽、不跑 claim/start**。

### 2. 定位现状

```
Grep / Glob 定位改动点 → Read 目标文件全文
```

- **读后写硬门**: 改任一文件前先 Read (漏读即改 → Edit 失配或覆盖)。

### 3. 执行改动

按 subtask 详情写码 / 改配置 / 跑命令。

- 命令带 `cwd` 指向工作目录; 记 exit code + 结果摘要。
- 命令失败 → `[工具失败: <命令 + 原因>]`, 不把报错当成功继续。
- 踩到可复用约定 → `skein-spec sediment --namespace=<ns> [--inclusion=always|auto] --category=<类目> --topic=<主题>` 落盘 (先 `skein-spec sediment --help` 核实参数)。

### 4. 自跑收尾 + 回传

按验收标准逐条对照 pass/fail。**改过的脚本必须先验证可运行才准报 done** (改 py 就跑 `python3 <改过的脚本> --help`; 改测试就跑 pytest 该文件), 跑不通一律 `subtask fail` 而非 `done`:

- 全 pass 且可运行 → `skein subtask done <tid> <sid>`
- 有 fail/缺信息 → `skein subtask fail <tid> <sid> --note "<原因>"`
- 附改动摘要 → 回传 JSON。

## 检查点

🛑 **改动范围由入参 `worktree` 字段决定, 不由路径长相决定** — `on` 时止步于 workdir, 不含主工作区; `off` 时在仓库根原地改。
🛑 **撤销改动只准 `git checkout -- <自己改的具体文件>` 逐个点名** — `git reset --hard` / `git reset` / `git clean` / `git stash` / `git checkout .` 不在允许范围内。原地态 (worktree 禁用) 下同一文件可能有并发或已完成 subtask 的改动, 全仓回滚会静默抹掉它们且无人发现。
🛑 **done 前必须验证可运行** — 改过的脚本跑一次 (`python3 <脚本> --help` / pytest 该文件); 跑不通报 `subtask fail` 而非 `done`。报了 done 却 import 就崩, 会让下游 subtask 基于不存在的符号写代码。
🛑 **读后写硬门** — 改前先 Read 目标文件。
🛑 **允许自跑 `subtask done/fail`；`create/start/check/finish/del` 等生命周期命令归 main**。
🛑 **缺信息标 `需要: <问题>` 回传, 由 main 转达用户** — 无 AskUserQuestion 权限。
🛑 **工具失败必标 `[工具失败: <原因>]`** — 命令失败/Read 不存在时, 只标 `[工具失败: <原因>]`, 不当成功结果返回 (原始错误输出不是有效结果)。
🛑 **exec 不勾 PRD 验收** — 正式验收归 check。scope 外问题另建 task, 不塞进当前 subtask。

## 失败模式 (if-then 三段式)

| 触发                  | 一线处理                     | 兜底                                                                |
| --------------------- | ---------------------------- | ------------------------------------------------------------------- |
| 验收标准不明          | 按最合理解释做 + note 标假设 | 判不准 → needs 标 `需要:`, subtask fail --note, status=需 main 介入 |
| 依赖文件/接口缺失     | Grep 全仓找替代              | 找不到 → needs 标缺失依赖, subtask fail, 不臆造                     |
| 命令报错              | 读报错定位, 修 1 次重跑      | 仍败 → `[工具失败: <原因>]` + subtask fail + status=需 main 介入    |
| 改动超出 subtask 范围 | 只做范围内, 范围外记 note    | needs 标「范围外发现」交 main 判是否拆新 subtask                    |
