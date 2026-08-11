---
name: skein-performance
description: 按 session 记录审计 skein 插件的行为偏差、Bug 与 token 浪费, 出可落地修复清单
argument-hint: "[claude code session-id] [--research]"
arguments: "[session-id]"
---

# skein 插件审计

对 session `$session-id` 审计 @@plugins/tools/skein/ 创建，产出**可复现的缺陷 + 对应修法**。

注意：

- 优化是整体优化而非对插件打补丁，不要存在就内容的说明，禁止出现变更日志类型、注释类型的东西在 Skill/Agent 中
- 提高插件效果、减少 token 浪费、避免重复计算 都是十分重要的目标
- 你可以使用 Skills('improve-codebase-architecture')、Skills('agent-reach') 等技能来优化插件性能

## 阶段 1 · 抽证据（先跑完这段，再决定读什么）

transcript 在 `~/.claude/projects/*/<session-id>.jsonl`，几十 MB。**禁止 Read 它，禁止 grep 全文**——下面几条 jq 就够撑起全部结论：

```bash
f=$(ls ~/.claude/projects/*/<session-id>.jsonl)

# 工具分布: Edit/Write 全在 main = executor 没被派 (本命指标)
jq -r 'select(.type=="assistant")|.message.content[]?|select(.type=="tool_use")|.name' $f | sort | uniq -c | sort -rn

# 子代理派发数 + 各自 prompt 长度 (派发失败常因 prompt 过长)
grep -c subagent_type $f

# skein 子命令频次: flow run / claim 的占比说明主循环有没有真的在跑
jq -r 'select(.type=="assistant")|.message.content[]?|select(.type=="tool_use" and .name=="Bash")|.input.command' $f \
  | grep -oE "skein [a-z]+ ?[a-z]*" | sort | uniq -c | sort -rn

# 串接违规 (flow-loop 禁 && 长链)
jq -r 'select(.type=="assistant")|.message.content[]?|select(.type=="tool_use" and .name=="Bash")|.input.command' $f \
  | grep skein | grep -cE "&&|\|\||;"

# 全部工具返回落盘, 后续只 grep 这个文件, 不再碰 jsonl
jq -r 'select(.type=="user")|.message.content[]?|select(.type=="tool_result")
       | if (.content|type)=="array" then ([.content[]|.text//""]|join("")) else (.content|tostring) end' $f > /tmp/tr.txt
grep -nE "Usage:|Error|无匹配|hook error|Unknown skill|exit code [1-9]" /tmp/tr.txt | head -40

# main 直接读写 .skein 的尝试 (hook 该拦而没拦 / 拦错了)
jq -r 'select(.type=="assistant")|.message.content[]?|select(.type=="tool_use")
       |select(.name|IN("Read","Write","Edit"))|.input.file_path' $f | grep '\.skein' | sort | uniq -c
```

## 阶段 2 · 交叉验证（判「是不是真 bug」，别靠读代码猜）

1. **先跑基线**：`cd plugins/tools/skein/scripts && uv run pytest -q --tb=line` + `uv run python -m mypy --strict --disable-error-code=untyped-decorator .`。红的先分类：stale test（引用已重构掉的路径/默认值翻转）vs 真缺陷。这一步找 bug 比读代码快一个量级。
2. **排除已修**：session 跑的多半是 `~/.claude/plugins/cache/ccplugin-market/skein/<sha>` 的旧副本。每条报错先在当前 master 复跑一遍，已修的不进清单（本轮实测：一半的 CLI 报错都已修）。
3. **落盘枚举对照**：hook/脚本里凡是拿状态串做判断的，核对 `task/model.py` 的 `TaskStatus`/`SubtaskStatus`——落盘是英文枚举，看板展示名是中文，写错就是永假的死分支（实测踩过两次）。
4. **可复现**：每条 bug 给一条能跑的最小复现（`/tmp` 建临时仓 + `skein.py` 直调），复现不出来的降级成「推测:」。

## 阶段 3 · 只答有证据的问题

**可答**：行为偏差（该派 agent 没派、该走 flow 走了 inline）、CLI 契约错配（参数猜错、报错文案不自足）、hook 该拦没拦、重复的 `--help` / 重复 IO、stale test、类型错误、文档与代码漂移。

**不可答，别列进输出**：内存占用、CPU 占用率、磁盘 IO、token 绝对数——transcript 里没有这些数据，写出来只能是编的。要测性能另开专项，用 `/usr/bin/time` 实跑，不从 session 记录里推。

## 调研

**默认不做**。只有带 `--research` 才派 agent-reach / octocode 查外部方案，且必须先写死检索关键词、限 15 分钟、无结论就直接说无结论。本轮实测：无约束的深度调研跑一小时零产出。

## 输出

一张表打头，然后两段。全文控制在 100 行内。

| #   | 位置 `file:line` | 现象 | 判定 | 修法 |
| --- | ---------------- | ---- | ---- | ---- |

- 判定只三种：`Bug`（有复现）/ `偏差`（与文档契约不符）/ `推测`（无复现，需人核）
- 「修法」一句话说清改哪、改成什么，不贴大段代码
- 表后接：**① 优先级**（高/中/低，各一行理由）**② 明确没做什么 + 为什么**

## 后续优化

如果用户接受了优化建议，使用 Agent 异步执行优化，但是不要使用 skein 来处理优化

#### 硬约束

- 先跑阶段 1 全部命令再动别的；不重复读同一文件，不重复 `--help`
- agent md / SKILL.md 按需读单个文件，禁 `cat agents/*.md` 一次性灌
- 每条结论挂 `file:line` 或工具输出；挂不上的前缀 `推测:`
- 报告只列本轮新发现；已在 master 修掉的写进「已闭环」一行带过，不展开
