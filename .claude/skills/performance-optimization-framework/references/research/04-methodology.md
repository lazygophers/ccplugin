# 04 · 跨栈通用性能优化方法论与历史共识

> 主题 Skill 顶层框架素材。本维度不绑定单一人物,提炼所有性能流派(系统/JVM/Web/SRE/算法)都认同的跨领域共识。
> 可信度标注:★★★(一手源:经典论文 / 本人原话 / 官方书) · ★★(权威二手:可信工程博客 / 教科书转述) · ★(普通二手:综述文章)
> 矛盾与争议予以保留,不强行调和。

---

## 一、跨栈共识方法论(核心)

所有性能流派反复收敛到同一套操作循环。无论 CPU profiling、JVM 调优、Web 前端、还是分布式系统,核心步骤一致。

### 1. 先建立基准 (Baseline),再谈优化

- 任何优化前先量化"现在多慢",定义可复现的测量环境与负载。没有 baseline 就无法证明优化有效,也无法发现回归。
- Brendan Gregg:"Measure early and often, but do not just throw fireballs of slow, bloated code into the world and hope to fix it later."(★★ koder.ai 转述 Gregg 观点)

### 2. 先度量 (Profile / Measure),禁止靠猜

- 这是跨流派最强共识。Rob Pike 规则 1:"You can't tell where a program is going to spend its time. Bottlenecks occur in surprising places, so don't try to second guess and put in a speed hack until you've proven that's where the bottleneck is."(★★★ Rob Pike, Notes on Programming in C, 1989)
- Rob Pike 规则 2:"Don't tune for speed until you've measured, and even then don't unless one part of the code overwhelms the rest."(★★★ 同上)
- Brendan Gregg 把"凭直觉试工具 / 无证据提假设"明确称为反方法论(anti-method),其 2013 Velocity 演讲直接命名为 **"Stop the Guessing"**。(★★★ Gregg, VelocityStopTheGuessing2013.pdf)
- Gregg 列出的反方法论:Blame-Someone-Else Anti-Method(甩锅)、Streetlight Anti-Method(只在自己熟悉的工具/路灯下找)、Ad Hoc Checklist Method。(★★★ Gregg, "Thinking Methodically About Performance", CACM 56(2):45-51, 2013)

### 3. 找瓶颈 / 热点 (Find the bottleneck)

- 优化分散在 5 处各砍 5% 几乎不改变用户可见延迟;真正的延迟通常被单一主导成本支配(一个热锁、一个慢依赖、一块过载磁盘、一种 GC 暂停模式)。先猎杀主导成本。(★★ koder.ai 转述 Gregg)
- 实战测试问题:"What could explain *most* of the latency change we're seeing?"(★★ 同上)
- 这是 Amdahl 定律(见下)在工程上的直接推论:优化非瓶颈部分,收益被其时间占比锁死。

### 4. 科学方法 (Hypothesis → Test → Verify → Iterate)

- Gregg 的 Scientific Method:把假设写成 **"If X, then we'd expect Y"**,做实验(可故意增/减性能)来确认或否定假设,使后续 USE/RED/profiling 更快——因为你已知假设成立时哪些数据该变。(★★★ Gregg LISA2012_methodologies.pdf;★★ koder.ai)
- 方法论的深层价值是**可复现 (repeatability)**:不依赖"谁直觉最强/嗓门最大",而是一致流程把问题收敛到具体资源/服务/代码路径。(★★ koder.ai)

### 5. 迭代验证回归

- 优化后回到第 1 步,用同一 baseline 验证收益为真、未引入回归。Jon Bentley《Writing Efficient Programs》的经典示范:对同一份代码(如 TSP)一次只应用一条性能规则,逐版迭代,最终提升 1+ 个数量级。(★★ HN 讨论转述 Bentley)

---

## 二、关键定律与公式

### Amdahl 定律 (1967) — 加速比上限

- 原论文:Gene M. Amdahl, **"Validity of the single-processor approach to achieving large scale computing capabilities"**, AFIPS Joint Spring Conference Proceedings 30 (Atlantic City, NJ, Apr. 18-20, 1967), pp. 483-485。(★★★ 出处确认)
- 核心:对系统单一部分优化所得的总体提升,被该部分实际占用时间的比例锁死。设可优化部分占比 p,加速 s,则总加速 = 1 / ((1-p) + p/s),s→∞ 时上限 = 1/(1-p)。
- 历史语境:1967 年 Amdahl 用此定律**反对**大规模并行处理。假设**固定问题规模**,给出悲观的扩展性。(★★ Wikipedia / nextplatform)

### Gustafson 定律 (1988) — 规模化加速

- 原论文:John L. Gustafson(与 Edwin Barsis,Sandia 国家实验室),**"Reevaluating Amdahl's Law"**, Communications of the ACM, 1988。(★★★)
- 动机:Gustafson 实测在 1024 处理器上获得 >1000 倍加速,看似"打破"了 Amdahl 定律。(★★ nextplatform)
- 核心差异:假设**问题规模随计算资源增长**(changing problem on changing hardware),串行部分不随并行部分增长,因此允许远高于 Amdahl 的有效加速,即"scaled speedup"。(★★ Wikipedia)
- **保留的矛盾**:有学者论证两律数学上等价,公开争论源于对两律本质的误解——前提是串行与并行程序对同一输入须计算相同总步数。(★★ Shi, "Reevaluating Amdahl's Law and Gustafson's Law", Temple CIS)

### Little 定律 (1961) — 排队系统普适关系

- 原论文:John D. C. Little, **"A Proof for the Queuing Formula: L = λW"**, Operations Research 9(3), pp. 383-387, 1961。(★★★ 出处确认)
- 公式:L = λW(系统内平均单元数 = 有效到达率 × 单元在系统内平均停留时间)。
- 普适性:**不受到达分布、服务分布、服务顺序影响**,适用于任意稳态系统及系统内的子系统。(★★ Wikipedia)
- 工程推论:并发 (concurrency) = 吞吐 × 延迟——延迟与吞吐是耦合变量,不是对立面。(★★ Medium/observabilityguy)
- 史:形式最早由 Philip M. Morse 在教科书中提出并"悬赏"反例,其博士生 Little 于 1961 给出广义证明;1972 Stidham 给出更直观证明,1974 给出 sample-path 版本。(★★ Wikipedia / Polaris)

---

## 三、核心信念(跨域复现 ≥ 2 领域)

每条均在至少两个独立性能流派中复现,可作为 Skill 顶层"通用信条"。

| 信条 | 复现领域 | 出处 |
|---|---|---|
| **测量先于优化,禁靠猜** | 算法(Pike/Bentley)+ 系统(Gregg)+ Web(性能预算) | Pike 规则 1-2 ★★★;Gregg Stop the Guessing ★★★ |
| **过早优化是万恶之源,但别放过关键 3%** | 算法(Knuth)+ 系统(Gregg "don't do it yet")+ 通用 | Knuth 1974 ★★★;Gregg ★★ |
| **优化收益被瓶颈占比锁死(聚焦主导成本)** | 并行(Amdahl)+ 延迟分析(Gregg)+ SRE | Amdahl 1967 ★★★;koder.ai ★★ |
| **延迟与吞吐是耦合 trade-off,非对立** | 排队论(Little)+ 系统设计 + SRE | Little 1961 ★★★;observability ★★ |
| **可观测性是一等公民,但本身消耗预算** | SRE(Golden Signals)+ Web(performance budget) | Google SRE ★★★;technori ★★ |
| **数据结构 > 算法(Data dominates)** | 算法(Pike 规则 5)+ Brooks《人月神话》 | Pike 规则 5 ★★★ |
| **简单算法优先,n 通常很小** | 算法(Pike 规则 3-4 = KISS)+ 工程实践 | Pike 规则 3-4 ★★★ |
| **关注尾延迟 (p95/p99) 而非均值** | SRE + 微服务监控 + Web | Splunk/RED ★★;Google SRE ★★★ |

### 系统级 trade-off(各流派共识)

- **延迟 vs 吞吐**:批处理↑吞吐但↑单请求等待;即时处理↓延迟但 worker 半数时间在上下文切换。系统接近容量时延迟自然上升,好设计是**控制**而非消除该 trade-off。(★★ observabilityguy/Medium)
- **空间 vs 时间**:缓存/预计算/查表用内存换 CPU(经典空间换时间);反向如压缩用 CPU 换带宽/存储。
- **可读性 vs 性能**:Knuth 原文的核心——非关键路径优化"在 debugging 和 maintenance 上有强烈负面影响",牺牲可读性须限定在已被测量证明的关键路径。(★★★ Knuth 1974)
- **尾延迟与扇出**:median 易达成易庆祝但脆弱;请求一旦依赖多个服务,尾延迟成为系统真实运行上限(fan-out 问题)。(★★ technori)

---

## 四、经典引用(带准确出处)

### Knuth「过早优化」全文(必给原始出处)

> "Programmers waste enormous amounts of time thinking about, or worrying about, the speed of noncritical parts of their programs, and these attempts at efficiency actually have a strong negative impact when debugging and maintenance are considered. **We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. Yet we should not pass up our opportunities in that critical 3%.** A good programmer will not be lulled into complacency by such reasoning, he will be wise to look carefully at the critical code; but only after that code has been identified."

- **原始出处**:Donald E. Knuth, **"Structured Programming with go to Statements"**, *ACM Computing Surveys* 6:4 (December 1974), pp. 261-301, §1。(★★★ 出处确认,Wikiquote + WebSearch 双重印证)
- **常被断章取义的关键**:孤立引用"premature optimization is the root of all evil"丢掉了后半句"Yet we should not pass up our opportunities in that critical 3%"——Knuth 主张的是**先识别关键代码再优化**,不是反对一切优化。
- **具体语境**:该句出现在 goto 论战中关于循环优化(loop unrolling)效率的讨论,Knuth 举例某优化只快 ~12%,很多人认为不值,但他强调关键路径仍要优化。(★★ effectiviology / slamdunk)
- **归属争议(保留)**:Knuth 15 年后在 "The Errors of TeX"(Software—Practice & Experience 19:7, July 1989)中称其为 "Hoare's Dictum",试图归给 Tony Hoare;但 Hoare 本人否认,Dijkstra 也被附会过。证据显示 Knuth 才是造句者。(★★ Wikiquote / slamdunk)
- **同一论文的另一变体**:"...premature optimization is the root of all evil (or at least most of it) in programming."(★★★ Wikiquote 引此为 1974 主句)

### Rob Pike 五条编程规则(1989)

> "Rule 1. You can't tell where a program is going to spend its time. Bottlenecks occur in surprising places, so don't try to second guess and put in a speed hack until you've proven that's where the bottleneck is.
> Rule 2. Measure. Don't tune for speed until you've measured, and even then don't unless one part of the code overwhelms the rest.
> Rule 3. Fancy algorithms are slow when n is small, and n is usually small...
> Rule 4. ...Use simple algorithms as well as simple data structures.
> Rule 5. Data dominates. If you've chosen the right data structures and organized things well, the algorithms will almost always be self-evident."

- 出处:Rob Pike, **"Notes on Programming in C"**, 1989。(★★★)
- 谱系:规则 1-2 重述 Hoare/Knuth 的过早优化箴言;规则 3-4 被 Ken Thompson 概括为 "When in doubt, use brute force",即 KISS;规则 5 早见于 Brooks《人月神话》。(★★ cs.unc.edu / Wikipedia)

---

## 五、方法论框架总结(USE / RED / TSA / Golden Signals)

四套监控/分析方法论,层次互补,是"可观测性 → 定位瓶颈"的通用工具箱。

| 方法 | 维度 | 提出者 / 出处 | 关注层 | 可信度 |
|---|---|---|---|---|
| **USE** | Utilization / Saturation / Errors | Brendan Gregg,"Thinking Methodically About Performance", CACM 56(2), 2013;brendangregg.com/usemethod.html | 硬件/基础设施资源(CPU/内存/磁盘/网络)——"服务器健康吗?" | ★★★ |
| **RED** | Rate / Errors / Duration | Tom Wilkie(Grafana),源自 Google Four Golden Signals | 请求驱动的微服务——"用户体验好吗?" | ★★ |
| **TSA** | Thread State Analysis(按线程状态分时) | Brendan Gregg,brendangregg.com/tsamethod.html | 应用线程(on-CPU vs SLP/阻塞),与 USE 资源视角互补 | ★★★ |
| **Four Golden Signals** | Latency / Traffic / Errors / Saturation | Google SRE Book, 2014, sre.google/sre-book | 用户面服务健康("若只能测 4 个指标,测这四个") | ★★★ |

- **USE 设计哲学**:像飞行手册的应急清单——simple, complete, fast。对每个资源查 利用率/饱和度/错误。利用率 100% 通常是瓶颈,I/O 资源 70%+ 常已是瓶颈。明确限制:USE 是早期粗筛,会漏掉某些问题,只是工具箱之一;先找到的问题可能是"一个"问题而非"那个"问题。(★★★ Gregg, FreeBSD Journal USE Method PDF)
- **TSA 两步**:① 对每个关注线程,测各线程状态总时长;② 从最频繁状态查到最少。与 Off-CPU 分析配合,使 100% 线程时间都可解释(CPU profiling 只看 on-CPU)。(★★★ brendangregg.com/tsamethod.html)
- **互补关系**:Golden Signals(用户面)+ USE(基础设施)+ RED(微服务)+ TSA(线程),多数团队同时用。(★★ Splunk / betterstack)

### 性能文化 / 性能预算 / 可观测性

- **性能预算 (performance budget)**:延迟预算不只是性能目标,而是架构优先级的压缩表达。(★★ technori)
- **可观测性悖论**:同步日志写入、高基数标签、逐请求全量 tracing 会把"可见性"变成可测量的用户延迟;事故期调高采样率正是系统最承受不起时。解法是 **budgeted observability**——智能采样、debug 模式与稳态埋点分离、明确哪些信号值得同步开销。(★★ technori)

---

## 六、来源清单(一手 / 二手 + URL)

### 一手源(经典论文 / 本人原话 / 官方书)— ★★★

1. Knuth, "Structured Programming with go to Statements", ACM Computing Surveys 6:4, Dec 1974, pp.261-301 — 过早优化原始出处。(经 Wikiquote 印证)https://en.wikiquote.org/wiki/Donald_Knuth
2. Knuth, "The Errors of TeX", Software—Practice & Experience 19:7, Jul 1989 — "Hoare's Dictum" 归属说法出处。
3. Amdahl, "Validity of the single-processor approach to achieving large scale computing capabilities", AFIPS 1967, pp.483-485 — Amdahl 定律原论文。
4. Gustafson & Barsis, "Reevaluating Amdahl's Law", CACM 1988 — Gustafson 定律原论文。
5. Little, "A Proof for the Queuing Formula: L = λW", Operations Research 9(3), 1961, pp.383-387 — Little 定律原证明。
6. Rob Pike, "Notes on Programming in C", 1989 — 五条规则原文。 https://www.cs.unc.edu/~stotts/COMP590-059-f24/robsrules.html
7. Brendan Gregg, "Thinking Methodically About Performance", Communications of the ACM 56(2):45-51, 2013, doi:10.1145/2408776.2408791 — 方法论/反方法论清单。
8. Brendan Gregg, "Stop the Guessing: Performance Methodologies for Production Systems", Velocity 2013 — https://www.brendangregg.com/Slides/VelocityStopTheGuessing2013.pdf
9. Brendan Gregg, "The USE Method", FreeBSD Journal 2014 + https://www.brendangregg.com/usemethod.html / use-linux.html
10. Brendan Gregg, "The TSA Method" — https://www.brendangregg.com/tsamethod.html
11. Brendan Gregg, LISA2012 Methodologies slides — https://www.brendangregg.com/Slides/LISA2012_methodologies.pdf
12. Google, "Site Reliability Engineering" (SRE Book), 2014, Monitoring Distributed Systems / Four Golden Signals — https://sre.google/sre-book/monitoring-distributed-systems/
13. Aleksey Shipilev, JMH 基准测试演讲(Devoxx/Øredev/JVMLS 2013)— https://shipilev.net/talks/devoxx-Nov2013-benchmarking.pdf(微基准陷阱权威一手源)

### 二手源(权威工程博客 / 教科书转述)— ★★

14. Wikiquote — Donald Knuth(全文 + 归属争议印证)https://en.wikiquote.org/wiki/Donald_Knuth
15. Wikipedia — Little's law / Gustafson's law(史与公式)https://en.wikipedia.org/wiki/Little%27s_law
16. Shi, "Reevaluating Amdahl's Law and Gustafson's Law", Temple CIS — 两律等价性争论(保留矛盾)https://cis.temple.edu/~shi/wwwroot/shi/public_html/docs/amdahl/amdahl.html
17. koder.ai — Brendan Gregg Performance Methods 综述(baseline/瓶颈/科学方法转述)https://koder.ai/blog/brendan-gregg-performance-methods-latency-profiling-bottlenecks
18. Oracle — "Avoiding Benchmarking Pitfalls on the JVM"(微基准陷阱)https://www.oracle.com/technical-resources/articles/java/architect-benchmarking.html
19. Java Code Geeks — "The Lies Your Microbenchmarks Tell You: A JMH Field Guide"(死代码消除/常量折叠/Blackhole)https://www.javacodegeeks.com/2026/05/the-lies-your-microbenchmarks-tell-you-a-jmh-field-guide-for-backend-engineers.html
20. Medium/97-Things — "Benchmarking Is Hard — JMH Helps"
21. Splunk / Better Stack — RED & USE & Golden Signals 对比
22. technori — "Latency Budget Trade-Offs That Break Systems at Scale"(性能预算/尾延迟/budgeted observability)https://technori.com/2026/04/25251-latency-budget-trade-offs-that-break-systems-at-scale/
23. observabilityguy/Medium — "The Throughput vs Latency Tradeoff"(Little's Law 耦合)https://observabilityguy.medium.com/the-throughput-vs-latency-tradeoff-most-developers-miss-04700bbd2a62
24. cs.unc.edu — Rob Pike's 5 Rules(原文托管 + 谱系注释)https://www.cs.unc.edu/~stotts/COMP590-059-f24/robsrules.html
25. effectiviology — Premature Optimization(Knuth 语境)https://effectiviology.com/premature-optimization/

---

## 七、缺口与待补

- **微基准陷阱**:已覆盖死代码消除/常量折叠/JIT 预热/Blackhole/@State 等核心陷阱(JMH 视角),但未深入到非 JVM 语言(C/C++ `-O2` 下编译器优化、Go benchmark `b.N` 机制、Rust criterion)。如需跨语言微基准章节,建议补 criterion / Go testing.B 一手文档。
- **Shipilev 演讲原文**:仅经 WebSearch 摘要确认,slides PDF 未逐页 fetch,引用细节(8-12× 失真倍数等)来自二手转述,标 ★★。
- **Amdahl/Gustafson/Little 原论文**:出处与摘要经多源印证,但 PDF 原文未直接 fetch(部分付费墙);公式与历史可信度高,具体页码以二手印证为准。
