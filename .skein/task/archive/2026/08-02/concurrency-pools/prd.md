# 并发池重构: work/gate 双池 + research 状态 — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标

一个 `max_active` 数字同时管三种互不相干的东西 (进行中 task 数、全局 running subtask 数、单 task
running subtask 数), 结果是: 想让验证多跑几个就得连带放开执行并发, 想收紧执行又会把验证一起卡死。
两类活的资源特征根本不同 —— 执行改码要独占工作树、彼此冲突, 验证只读、天然可并行。

本次把单一上限拆成**按活的性质分的两个池**, 并给 research 与收尾这两个「实际存在但引擎看不见」
的阶段补上状态载体, 让它们能被真正计数和调度。

- [x] **work 池 (2)**: exec 与 research 共享。两者都在改/读工作树, 抢的是同一份注意力与磁盘。
- [x] **gate 池 (3)**: check 与 finish 共享。都是只读验证/收尾, 可以放得更宽。

顺带清掉两处历史包袱: 「就绪」这个只存在于 confirm 与 start 之间、没人真正停留的中间态; 以及
research 至今没有状态、只能靠人记着「这个 task 还在查资料」的窘境。

成功长这样: 配置里两个数字各管各的, 调大 gate 不影响 exec; `claim` 能同时调度 exec 与 research
两类 subtask 且 exec 优先出线; 一个 task 从创建到完成全程有状态可查, 没有「引擎不知道它在干嘛」
的空窗。

## 边界

**范围内**
- [x] task 状态机改造: 删「就绪」, 加「调研中」「收尾中」
- [x] `skein start` 并入 `confirm` (人审门 = 状态转换, 一步到位)
- [x] subtask 新增 `phase` 字段 (exec | research)
- [x] `max_active` 换成 `pools.work` / `pools.gate` 两键
- [x] work 池调度改加权打分 (等待时间 + 关键路径权重 + 类型加权)
- [x] 全部下游同步: 体检、看板、Web 视图、注入文案、skill/agent 文档、测试

**范围外 (非目标)**
- [x] 不改 subtask DAG 的依赖语义 (`depends_on` 怎么算就绪不动)
- [x] 不改 worktree 生命周期本身 (只改由谁触发建/销)
- [x] 不引入 subtask 级的独立优先级字段 —— 「优先级」沿用现有关键路径权重
- [x] 不做池的动态伸缩 / 按机器负载自适应
- [x] 不改 spec 子系统

**已知约束**
- [x] `max_active` 直接删除, 不留 deprecated fallback (用户明确要求)。已有工作区的
  `.skein/config.yaml` 升级后并发限制会静默变回默认值 —— 需在 doctor 里给出可见提示。
- [x] 「收尾中」必须是**独立一步**才有意义: 引擎看不见 main 派出去的 finisher agent, 只有先占槽
  再派, 才谈得上限制并发 finisher。
- [x] 工作区 flock 仍在, 与池正交: 池限的是同时干活的 agent 数, 锁防的是并发写 task.json。

## User Stories

1. As a 调度者, I want exec 与 research 的 subtask 在同一个 work 池里竞争, so that 我不会因为
   开了两个调研就没法执行代码。
2. As a 调度者, I want exec 类 subtask 在同分条件下先出线, so that 主线进度不被调研饿住。
3. As a 调度者, I want 等得久的 subtask 分数逐渐升高, so that 低关键路径权重的活不会永远排不上。
4. As a 验证者, I want check 与 finish 走独立的 gate 池, so that 我可以同时验三个 task 而不占用
   执行槽。
5. As a 使用者, I want task 创建后先进 plan 态, so that 「还在规划」和「已经开工」不再混为一谈。
6. As a 使用者, I want 在 plan 态规划出 research subtask 后能把 task 推进 research 态, so that
   调研本身也走 DAG 调度而不是靠人记。
7. As a 使用者, I want research 过程中还能增删 research subtask, so that 查到一半发现要多查一样
   东西时不必先退出 research 态。
8. As a 使用者, I want research 态**禁止**直接进开工态, so that 调研完必须回 plan 做规划/总结/
   设计, 不会查完资料就闷头开写。
9. As a 使用者, I want plan 与 research 之间可以来回切, so that 规划中发现信息不足能再退回去查。
10. As a 使用者, I want `confirm --approved` 一步把 task 推进开工态, so that 我不用记「confirm
    完还要再 start 一次」。
11. As a 收尾者, I want 先占 gate 槽标「收尾中」再派 finisher, so that 并行收尾的数量真的受限。
12. As a 体检者, I want doctor 发现某个池超限时报出来, so that 手工改坏 task.json 能被发现。
13. As a 看板读者, I want 看板与 Web 视图显示两个池各自的占用/上限, so that 我一眼看出卡在哪个池。
14. As a 老工作区用户, I want 升级后 doctor 提示 `max_active` 已废弃, so that 我知道要去改配置而
    不是纳闷并发怎么变了。
15. As a 调度者, I want `claim` 在两个池都满时分别说明是哪个池满, so that 我知道该 finish 一个还
    是该 done 一个。
16. As a 边界情况, task 在 research 态时 `confirm` 应当被拒绝并提示先回 plan。
17. As a 边界情况, research subtask 未全 done 时退回 plan 应当被拒绝 (或明确允许并说明后果)。
18. As a 边界情况, work 池满而 gate 池空时, check 类操作不应被 work 池阻塞。

## 验收标准

- [x] task 状态枚举为: 待处理 / 调研中 / 进行中 / 检查中 / 收尾中 / 已完成 —— 「就绪」不再出现在
      任何枚举、别名表、排序表、阶段映射中
- [x] `skein start` 命令已删除, 其全部职责 (体检 / prd double-check / worktree / started 时间戳 /
      start 阶段钩子) 由 `confirm --approved` 承担, 且 confirm 后 task 直接处于开工态
- [x] subtask 有 `phase` 字段, 取值 exec | research, 缺省为 exec (老数据免迁移)
- [x] `pools.work` / `pools.gate` 两键生效; `max_active` 在代码中零残留
- [x] work 池计数 = 全局 phase ∈ {exec, research} 的 running subtask 数, 上限 `pools.work`
- [x] gate 池计数 = 处于「检查中」+「收尾中」的 task 数, 上限 `pools.gate`
- [x] 两池互不影响: work 满时仍可 check; gate 满时仍可派 exec
- [x] work 池出线顺序由加权分决定, 分数含等待时长、关键路径权重、类型加权三项, 且 exec 类在
      其余条件相同时排在 research 之前
- [x] 等待足够久的 research 能越过刚入队的 exec (证明不是硬抢占, 无饿死)
- [x] `研究中` task 调用 confirm 被拒, 错误信息指明先回 plan
- [x] plan ⇄ research 双向转换可用, 且 research → 开工态 无直达路径
- [x] 「收尾中」为独立状态, 占 gate 槽, 由独立命令进入; finish 从「收尾中」完成闭环
- [x] doctor 检出任一池超限并报错; 检出配置里残留 `max_active` 并提示已废弃
- [x] 看板与 Web 视图显示两池各自 占用/上限
- [x] `claim` 满槽时的提示能区分是 work 满还是 gate 满
- [x] 全部 skill / agent / 文档中的「就绪」「start」「max_active」表述已同步
- [x] 全量测试通过, ruff F/E9 清白

## Testing Decisions

只测外部行为: 给定一组 task/subtask 状态, 断言 `claim` 返回哪些、`confirm` 放行还是抛错、doctor
报不报错。**不测**打分函数的具体数值 —— 那是实现细节, 常数一调测试就红, 但真正要保住的性质只有
三条: exec 同分优先、等待能翻盘、池上限不被突破。这三条各写一个行为测试。

状态机测试沿用现有 `tests/test_*.py` 里 `ws` fixture 起临时工作区、跑真实 CLI 子进程的先例 ——
不 mock, 因为状态转换的真值在落盘的 task.json 上, mock 掉就等于没测。

必须有一个测试钉住「`max_active` 零残留」(源码扫描), 否则删一半漏一半, 老键在某个分支里还活着,
行为会诡异地时对时错。

同理钉住「就绪 / start 零残留」—— 这类字符串散落在 skill/agent/文档里, 靠人肉 grep 必漏。

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list concurrency-pools`)
