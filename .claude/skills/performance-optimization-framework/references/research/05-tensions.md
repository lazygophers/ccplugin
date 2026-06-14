# 性能优化领域的内在张力与反模式

> 调研维度：性能优化各流派之间、以及与主流软件工程观点的「分歧、争议、反模式」。
> 用途：为 performance-optimization-framework 主题 Skill 提供「内在张力」与「反模式」章节素材。
> 原则：**保留矛盾本身**，不和稀泥。每条标来源与可信度。明确区分「真实公开争论」与「我推断的张力」。

---

## 一、核心分歧（成对呈现）

### 分歧 1：「过早优化是万恶之源」—— 被滥用的引用 vs 原意

**A 派（流行解读 / 被滥用版）**：「Premature optimization is the root of all evil」被截断成一句口号，用来论证"性能根本不该提前考虑"、"先写干净代码，性能以后再说"，甚至变成"永远别优化"的借口。

**B 派（Knuth 原意 + 反方）**：Knuth 的原文恰恰在**捍卫合理的效率追求**，只是反对在非关键路径上瞎操心。被丢掉的关键限定词是「97%」和「关键的 3%」。

Knuth 1974 年原文（一手）：
> "We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. **Yet we should not pass up our opportunities in that critical 3%.** A good programmer will not be lulled into complacency by such reasoning; he will be wise to look carefully at the critical code; **but only after that code has been identified.**"
> — Donald Knuth, "Structured Programming with go to Statements", *ACM Computing Surveys* 6:4 (Dec 1974), §1, pp. 261–301.

Knuth 同一篇里直接抨击了**反向极端**：
> "the conventional wisdom shared by many of today's software engineers calls for ignoring efficiency in the small; but I believe this is simply an overreaction to the abuses they see being practiced by penny-wise-and-pound-foolish programmers, who can't debug or maintain their 'optimized' programs."

要点：
- Knuth 本人不主张原创权，15 年后称之为「Hoare's Dictum」（归功 Tony Hoare）。
- 滥用的核心是**只引前半句、丢掉「关键 3%」与「先定位再优化」**。
- Knuth 的真实立场更接近 B 派：在已成熟工程里 "a 12% improvement, easily obtained, is never considered marginal"。

> 真实争论标记：**真实**。这是公开、反复被引用的考据，HN 与多篇博客均做过原文还原。

---

### 分歧 2：过早优化 vs 过早劣化（premature pessimization）

**A 派（避免过早优化）**：别为想象中的大数据量提前上复杂算法、牺牲可读性。

**B 派（避免过早劣化，Sutter / Alexandrescu）**：「不要过早优化」**不等于**可以随手写低效代码。在复杂度和可读性都不变的前提下，高效写法应当"自然从指尖流出"，刻意写笨代码反而是错。

C++ Coding Standards Item 9「Don't pessimize prematurely」（一手）核心：
> "By premature pessimization we mean writing such gratuitous potential inefficiencies as: defining pass-by-value parameters when pass-by-reference is appropriate; using postfix ++ when the prefix version is just as good; using assignment inside constructors instead of the initializer list."
> "It is not premature optimization to … pass by reference, to prefer calling prefix ++ … These are not premature optimizations; they are simply avoiding premature pessimizations."

对称命题：
> "It would clearly be wrong to optimize prematurely … But it would equally clearly be wrong to **pessimize prematurely** by turning a blind eye to algorithmic complexity (big-Oh)."
> — Herb Sutter & Andrei Alexandrescu, *C++ Coding Standards*, Item 9 (Addison-Wesley, 2004/2005).

要点：这一对是「过早优化」口号最直接的纠偏。两者构成**双侧约束**：既不为臆想优化、也不为显摆"不优化"而劣化。库开发场景下天平偏向效率，因为调用上下文未知。

> 真实争论标记：**真实**（书中明确成文的对立概念，非我编造）。

---

### 分歧 3：抽象/可维护性优先 vs 数据导向/性能优先（DOD vs OOP）

**A 派（Clean Code / OOP / 可维护性派，Robert "Uncle Bob" Martin）**：
- 多数软件用不到 1% 的 CPU，省程序员的时间比省机器周期更经济。
- 先为可读性写，需要时再优化。多态、依赖倒置带来的灵活性值这个代价。
> "It is economically better for most organizations to conserve programmer cycles than computer cycles." — Uncle Bob, cleancodeqa 讨论。

**B 派（Data-Oriented Design，Mike Acton）**：
- 程序的唯一目的是**数据变换**；不理解硬件就无法推理代价。
- 抨击 C++ 文化的「Three Big Lies」（软件是平台 / 代码先于数据设计 / 代码才是重点）。
> "If you don't understand the cost of solving the problem, you don't understand the problem. If you don't understand the hardware, you can't reason about the cost of solving the problem."
> "Solving problems you probably don't have creates more problems you definitely do."
> — Mike Acton, "Data-Oriented Design and C++", CppCon 2014 keynote.
- 经典反例：游戏里 `physicsChair / breakableChair / staticChair` 强行继承 `Chair` 是坏主意——引擎代码里它们几乎无共性；按数据布局对齐 cache line 可带来 10x+ 加速。

**B 派延伸（Casey Muratori，"Clean Code, Horrible Performance"）**：
- 直接拿 Clean Code 书中的例子跑 benchmark，论证多态/小函数拆分让程序慢一个数量级。
- 重构本身改变了机器层面的程序："把一个循环拆成两个循环……（若编译器无法 fuse）字面上就是不同的程序。"
> "software is getting unusably slow these days, even for simple tasks" — Casey Muratori, cleancodeqa。

收敛点（双方都让一步）：Bob 承认性能意识在教学中应更突出；Casey 承认在非性能关键系统里生产力收益成立。

> 真实争论标记：**真实**。Uncle Bob 与 Casey 在 GitHub（unclebob/cmuratori-discussion）有公开逐条往返，并有 SE Radio 577 播客跟进。Acton 的 keynote 是公开一手。

---

### 分歧 4：自上而下（先找系统瓶颈）vs 自下而上（逐行/微优化）

**A 派（自上而下，Brendan Gregg）**：
- 先用方法论提出"该问系统什么问题"，**再**伸手抓工具，而非抓着喜欢的工具到处找问题。
- USE Method：对每个资源查 Utilization / Saturation / Errors，快速定位系统级瓶颈。
> "focuses on the questions to ask of the system, before reaching for the tools."
> — Brendan Gregg, "Thinking Methodically About Performance" / USE Method (brendangregg.com, USENIX LISA12)。
- 反对"无方法论硬猜"：performance engineers 可能在单个问题上耗半年无果，不如试一周就换方向。

**B 派（自下而上 / 贴硬件，Martin Thompson 机制同理心 + Acton DOD）**：
- 从 CPU-内存关系、cache 层级、写竞争出发设计数据结构（LMAX Disruptor：三级流水线延迟比队列方案低 3 个数量级，50ns 级延迟）。
> "applying an understanding of the hardware to the creation of software [is] fundamental to delivering elegant high-performance solutions." — Martin Thompson, mechanical-sympathy 博客。

张力本质：Gregg 的方法论是「先全局测量定位、避免凭直觉优化」；Thompson/Acton 是「从硬件第一性原理向上设计」。前者天然防御"瞎猜微优化"反模式；后者主张某些性能必须在架构期就贴硬件设计，事后 profiling 救不回来。

> 标记：**部分真实、部分我推断的张力**。Gregg「先问问题再抓工具」是其明确立场（真实）；Thompson「机制同理心」是其明确立场（真实）。但把二者直接对立成"自上而下 vs 自下而上"是**我归纳的张力框架**——两人并未公开互相点名辩论，实践中也常互补（先测量定位热点，再贴硬件重写热点）。

---

### 分歧 5：微基准（microbenchmark）vs 真实负载（macrobenchmark）

**A 派（微基准有用派）**：像单元测试一样隔离测单个方法/小逻辑，快速对比候选实现。

**B 派（微基准误导派）**：JVM/硬件是自适应激进优化的运行时，隔离测量会被多种优化扭曲，数字"看着可信但根本误导"。

JMH 文档自我警告（一手）：
> "the numbers below are just data. To gain reusable insights, you need to follow up on why the numbers are the way they are."

主要陷阱：
- **Dead Code Elimination**：结果没被消费，编译器合法删掉你要测的计算——可让 benchmark 假快 8–12×。修法：返回结果或用 `Blackhole.consume()`。
- **Constant Folding**：常量入参被折叠，计算其实没发生。
- **JIT warm-up**：稳态前测量，多种执行模式被平均成无意义数。
- **False sharing / scope 错误**：多线程下 cache line 邻近导致伪竞争；state scope 错误模拟了与生产完全不同的共享模式。

要点：微基准误导的根因是"小程序邀请了真实负载里不会发生的过度优化"。准确的前提是**忠实复现生产执行条件**——而这恰恰是微基准最难做到的。

相关但本轮未取证：Gil Tene 的「Coordinated Omission」（延迟测量系统性漏掉慢请求，导致 P99 被严重低估）—— 与本对张力高度相关，属同一主题但本次搜索未命中一手源。**缺口，见下。**

> 标记：**真实**（JMH 陷阱是公认工程事实，文档与多篇技术文一致）。

---

## 二、常见反模式清单

1. **断章取义引用 Knuth**：只引「premature optimization is the root of all evil」，丢掉「97% / 关键 3% / 先定位再优化」，把它当"永不优化"挡箭牌。（分歧 1）
2. **过早劣化（Premature Pessimization）**：以"避免过早优化"为名随手写低效代码——值传递该用引用、用 assignment 不用初始化列表、对 big-Oh 视而不见。（分歧 2）
3. **瞎猜式优化 / 工具先行**：不先测量定位，抓着喜欢的 profiler 到处找问题，在非热点上耗时。（Gregg，分歧 4）
4. **微基准当结论**：把被 DCE/常量折叠/未热身污染的微基准数字当真实性能；不复现生产条件。（分歧 5）
5. **数字不追因**：拿到 benchmark 数字直接下结论，不问"为什么是这个数"。（JMH 自警）
6. **过度通用化**：为大概率不会出现的需求/数据量提前上泛化抽象（"solving problems you probably don't have"）。（Acton）
7. **臆想硬件**：自以为有机制同理心，实则基于多年前过时的硬件模型推理。（Thompson / Fowler）
8. **过早优化非性能维度**：把可维护性、灵活性、安全、健壮性也过早优化（over-abstraction、过度防御）。（Carmack，见下引用）

---

## 三、争议性引用（带出处）

> "You can prematurely optimize maintainability, flexibility, security, and robustness just like you can performance."
> — John Carmack（Twitter/X，扩展 Hoare/Knuth 命题）。**把"过早优化"反过来指向抽象党本身**。

> "In almost all cases, directly mutating blocks of memory is the speed-of-light optimal case, and avoiding this is spending some performance. … you can write a pure DrawTriangle() function that … returns a completely new framebuffer … Don't do that."
> — John Carmack, "On Inlined Code"（2007 邮件 + 2014 注解）。Carmack 既拥抱函数式（消除意外状态突变），又坦承其性能代价；2014 反思："the style gets applied as a matter of course in many cases where a performance benefit is negligible, but we still eat the bugs."（**连他自己都承认函数式被过度套用**。）

> "the programmer's job is NOT to write code; the programmer's job is to solve (data transformation) problems." / "The Three Big Lies."
> — Mike Acton, CppCon 2014。直接挑战"代码/抽象本身是目的"的主流叙事。

> "Many programmers think they have mechanical sympathy, but it's built on notions of how hardware used to work that are now many years out of date."
> — Martin Fowler 转述 Martin Thompson，"The LMAX Architecture"。

> "It is economically better for most organizations to conserve programmer cycles than computer cycles."
> — Robert C. Martin（cleancodeqa 讨论）。可维护性派的经济学核心论点。

---

## 四、来源清单（标一手/二手 + URL + 可信度）

| # | 来源 | 类型 | URL | 可信度 |
|---|------|------|-----|--------|
| 1 | Knuth, "Structured Programming with go to Statements", ACM Computing Surveys 6:4 (1974) | **一手**（原论文） | 见 Wikiquote 转录 https://en.wikiquote.org/wiki/Donald_Knuth | 高（原文权威，转录广泛核对） |
| 2 | Knuth 引用考据（HN 讨论 / hlopko.com / joshbarczak） | 二手（考据） | https://news.ycombinator.com/item?id=44386236 ; https://hlopko.com/2019/08/03/premature-optimization/ ; http://www.joshbarczak.com/blog/?p=580 | 中高（多源交叉一致） |
| 3 | Sutter & Alexandrescu, *C++ Coding Standards*, Item 9 "Don't pessimize prematurely" (2004/05) | **一手**（书） | https://ebookreading.net/view/book/EB0321113586_19.html ; 全书 PDF http://library.bagrintsev.me/CPP/Sutter.C++%20Coding%20Standards.2005.pdf | 高（书中原文） |
| 4 | Mike Acton, "Data-Oriented Design and C++", CppCon 2014 keynote（视频+slides） | **一手**（演讲） | https://www.youtube.com/watch?v=rX0ItVEVjHc ; slides https://github.com/CppCon/CppCon2014/tree/master/Presentations/Data-Oriented%20Design%20and%20C++ | 高 |
| 5 | Uncle Bob ↔ Casey Muratori, "Clean Code, Horrible Performance" 公开往返 | **一手**（双方原话） | https://github.com/unclebob/cmuratori-discussion （cleancodeqa.md） | 高（当事人逐条记录） |
| 6 | SE Radio 577: Casey Muratori on Clean Code, Horrible Performance | 二手（访谈） | https://se-radio.net/2023/08/se-radio-577-casey-muratori-on-clean-code-horrible-performance/ | 中高 |
| 7 | Brendan Gregg, USE Method / "Thinking Methodically About Performance" (USENIX LISA12) | **一手**（作者本人页 + 会议） | https://www.brendangregg.com/methodology.html ; https://www.usenix.org/conference/lisa12/performance-analysis-methodology | 高 |
| 8 | Martin Fowler, "The LMAX Architecture"（转述 Thompson 机制同理心） | 二手（权威转述） | https://martinfowler.com/articles/lmax.html | 高 |
| 9 | LMAX Disruptor 官方文档（机制同理心实战 + 延迟数据） | **一手** | https://lmax-exchange.github.io/disruptor/ | 高 |
| 10 | John Carmack, "On Inlined Code"（2007 邮件 + 2014 注解，Jonathan Blow 托管） | **一手**（作者邮件） | http://number-none.com/blow/blog/programming/2014/09/26/carmack-on-inlined-code.html ; 全文 https://cbarrete.com/carmack.html | 高 |
| 11 | Carmack「prematurely optimize maintainability…」引用 | 一手原话 / 二手聚合 | https://www.azquotes.com/quote/1393876 | 中（聚合站，引用本身真实可查 Twitter 出处） |
| 12 | JMH 微基准陷阱（DCE / constant folding / warmup / false sharing） | 二手（技术文，转述 JMH 官方告诫） | https://www.javacodegeeks.com/2026/05/the-lies-your-microbenchmarks-tell-you-a-jmh-field-guide-for-backend-engineers.html ; https://www.codecentric.de/wissens-hub/blog/performance-measurement-with-jmh-java-microbenchmark-harness ; demo https://github.com/rucek/jmh-demo | 中高（与 JMH 官方文档一致） |

共 12 条来源，其中一手 ≥ 8 条。黑名单（知乎/公众号/百度百科）未使用。

---

## 五、缺口与待补（不编造）

- **Gil Tene「Coordinated Omission」/「How NOT to Measure Latency」**：与「微基准 vs 真实负载」「延迟测量」高度相关的一手源，本轮搜索未命中。建议后续单独取证（HdrHistogram、Azul、其 QCon/Strange Loop 演讲）。
- **分歧 4（自上而下 vs 自下而上）的"对立"是我归纳的框架**：Gregg 与 Thompson 各自立场真实，但二者并无公开互相点名的辩论；实践中常互补。Skill 中应如实标注为"张力/取向差异"而非"公开争论"。
- **各流派对工具的偏好分歧** 仅间接覆盖（Gregg=DTrace/perf/火焰图、Java 系=JMH、DOD/游戏=自研 profiler + cache 分析）：未做专门取证，若需成章建议补一轮。
- **「性能文化应多早介入」**：已被分歧 1/3（先写干净 vs 趁早设计）间接覆盖，但缺独立的"性能左移 / 性能预算（performance budget）"一手源（如 Addy Osmani / Souders 的 RAIL、performance budget 文章）——前端流派一手源本轮未专门取，是明显缺口。
