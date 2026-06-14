# 流派调研 03：低延迟 / 高并发工程（Mechanical Sympathy 学派）

> 调研主题：以 Martin Thompson（LMAX Disruptor 作者、Mechanical Sympathy 博客）为代表的低延迟/高并发工程方法论。
> 旁系代表：Mike Acton（Data-Oriented Design）、Gil Tene（尾延迟度量）。
> 标注约定：每条标注【一手】（本人原话/原始论文/原始演讲）/【二手】（他人总结）/【推测】。可信度 = 来源权威性 + 是否本人直述。

---

## 核心方法论

### 1. Mechanical Sympathy（机械同理心）——理解硬件来写软件
理解底层硬件的工作方式，写出与硬件协同（而非对抗）的代码。命名借自 F1 车手 Jackie Stewart：最好的车手懂机器原理，从而与机器和谐配合。
- 【一手】Thompson 原话："I want to try and produce software which does justice to the wonderful achievements of our hardware friends."（来源 S1）
- 【一手】动机引用 Petroski："The most amazing achievement of the computer software industry is its continuing cancellation of the steady and staggering gains made by the computer hardware industry."（Thompson 在 S1 引用，用以表达：软件不断抵消硬件进步，不必如此）
- 【二手】Martin Fowler 站点将其蒸馏为四条原则：可预测内存访问 / 缓存行意识 / 单写者原则 / 自然批处理（来源 S8）

### 2. 缓存行与 False Sharing（伪共享）规避
- 缓存行是缓存一致性的基本单位（x86 通常 64 字节）。两个变量落在同一缓存行、被不同线程写，即使逻辑无关也会像写同一变量一样产生写竞争——这就是 false sharing。
- 【一手/原始论文】Disruptor 论文："if two variables are in the same cache line, and they are written to by different threads, then they present the same problems of write contention as if they were a single variable. This is a concept know as 'false sharing'."（来源 S2）
- 【二手】Thompson 称 false sharing 为 "the silent performance killer"（沉默的性能杀手），因为看代码完全看不出来（来源 S5 转述其博客）
- 缓存行 ping-pong：发生 false sharing 时缓存行经 L3 来回弹跳；跨 socket 还要过 interconnect，代价更大（来源 S5）
- 规避手段——cache line padding（缓存行填充）：在跨线程的计数器/指针字段之间填充，使其各占独立缓存行。
  - 【一手】Thompson："If you have counters or pointers that are used across threads it is vitally important to ensure they are in different cache lines or the application will not scale up with cores."（来源 S5 转述其 2011-07 "False Sharing" 博客）
  - 【一手/矛盾点】Java 7 把"无用 long 字段"优化掉/重排，导致 padding 失效、false sharing 复发；Thompson 后续改用 PaddedAtomicLong 方案（来源 S5 转述其 2011-08 "False Sharing && Java 7"）。**矛盾保留**：他的早期"填 7 个 long"方案在 Java 7 上不可靠，需实测验证。
  - padding 大小经验值：64 字节通常够；要兼容"相邻两缓存行作为一致性单位"的处理器则用 128 字节（来源 S5 邮件列表讨论）

### 3. LMAX Disruptor——无锁环形缓冲区设计
高性能交易所的核心数据结构，替代有界队列在并发线程间交换数据。原始论文作者：Martin Thompson, Dave Farley, Michael Barker, Patricia Gee, Andrew Stewart（v1.0, 2011-05，来源 S2）。
关键设计点（全部【一手/原始论文】，来源 S2）：
- **预分配环形缓冲（pre-allocated ring buffer）**："At the heart of the disruptor mechanism sits a pre-allocated bounded data structure in the form of a ring-buffer." 启动时全部内存预分配。
- **GC 友好**："The pre-allocation of entries in the ring buffer means that it is immortal as far as garbage collector is concerned and so represents little burden."
- **单写者**："the ideal algorithm would be one with only a single thread owning all writes to a single resource with other threads reading the results"，"eliminating write contention"。
- **Sequencing（序号）**："Sequencing is the core concept to how the concurrency is managed in the Disruptor." 生产者顺序认领槽位，再通过 memory barrier 提交（而非每次 CAS）。
- **分离关注点**：队列把"存储 / 生产者协调 / 消费者通知"三件事耦合在 head/tail/size 上；Disruptor 把它们拆开。
- **性能结论**："the mean latency using the Disruptor for a three-stage pipeline is 3 orders of magnitude lower than an equivalent queue-based approach"；吞吐约 8 倍（对比 ArrayBlockingQueue，来源 S2/S0）。
- **为什么队列差**（来源 S2）："Queue implementations tend to have write contention on the head, tail, and size variables." 且 "Queues are typically always close to full or close to empty ... They very rarely operate in a balanced middle ground."；Java 中队列还是 "significant sources of garbage"。
- 【二手/矛盾点】独立评审 Evan Jones 指出论文夸大了锁的代价：论文称 mutex 仲裁需 context switch 到内核，但实际只在**竞争时**才进内核；未竞争的 pthread mutex / Java 同步走 x86 CAS，不进内核。结论："locks are expensive, but they aren't as expensive as the small microbenchmark presented makes it seem."（来源 S3）。**矛盾保留**。

### 4. 单写者原则（Single Writer Principle）
- 【一手】核心论点："the single biggest limitation on scalability is having multiple writers contend for any item of data or resource."；反转思路：让每个数据/资源只被单一写者修改（来源 S6）。
- 【一手】竞争代价的实测（2.4GHz Westmere，自增 64 位计数器 5 亿次，来源 S6）：单线程 300ms；两线程加锁 118,000ms（约 394 倍慢）。
- 【一手】队列效应："Those waiting to enter the critical section ... must queue, and this queueing effect (Little's Law) causes latency to become unpredictable and ultimately restricts throughput."（Little's Law / 排队论解释延迟不可预测，来源 S6）
- 【一手】单写者为何 scale："each execution context can spend all its time and resources processing the logic for its purpose, and not be wasting cycles ... on dealing with the contention problem."；多读者无妨——"CPUs can broadcast read only copies of data to other cores via the cache coherency sub-system ... it scales very well."（来源 S6）
- 【一手】锁/无锁的分工建议：lock-free 算法极难证明正确，**不应用于业务逻辑**，只用于底层基础设施组件；业务逻辑跑在单线程上、遵循单写者原则（来源 S6 转述其低延迟文章）。

### 5. 自然批处理（Natural Batching）
- 【二手/Fowler 蒸馏】单写者处理批次时贪婪构建：有数据立刻开批，队列空或批满即收。对比定时器（timeout）批处理，自然批处理同时改善延迟（best 100µs / worst 200µs，对比 timeout 200/400µs，来源 S8）。
- 【一手】Thompson 有专门博客 "Smart Batching"（2011-10，来源 S6 列出，未深读原文）。

### 6. 数据导向设计（Data-Oriented Design，Mike Acton 视角）
游戏引擎/性能关键领域的方法论，与 Mechanical Sympathy 同源（都以硬件现实为出发点）。
- 【一手】核心断言："The purpose of all programs, and all parts of those programs, is to transform data from one form to another."（CppCon 2014，来源 S7）
- 【一手】"If you don't understand the data, you don't understand the problem."；"Different problems require different solutions. If you have different data, you have a different problem."（来源 S7）
- 【一手】"Three Big Lies"（源自 2008 CellPerformance 博客，CppCon 2014 重述，来源 S7）：
  1. Software is a platform（错：真正的平台是硬件，相信软件是平台就是无视现实）。
  2. Code should be designed around a model of the world（错：现实世界的 IS-A 不等于软件里的 IS-A；Chair/PhysicsChair/StaticChair/BreakableChair 在数据变换层面几乎毫无共性，不该因现实相似就建类层级）。
  3. Code is more important than data（错："Code is ephemeral and has no real intrinsic value." 数据才是本质）。
- 【二手】DOD 实践中常见 10x 提升，靠的是面向数据使用模式做相对简单的变换（如 SoA 替代 AoS、提升内存连续性，来源 S7）。

### 7. GC 调优与对象分配规避（机制 over 框架）
- 【一手】"Java Garbage Collection Distilled"（2013-07，博客+InfoQ，来源 S9）：GC 频率直接由分配速率（bytes/秒）决定，分配越快、young gen 回收越频繁；调优常需改应用代码以**降低对象分配率/对象生命周期**。
- 【一手】极端低延迟下若分配/晋升率过高，调优可能无解，需商业权衡——买并发压缩 JVM（JRockit Real Time / Azul Zing，来源 S9）。
- 【一手】Time To Safepoint (TTSP)：拷贝大数组、克隆大对象、有限计数循环可能数毫秒才到 safepoint，是低延迟应用的重要考量；线程越多，stop-the-world 后恢复调度压力越大——少依赖 STW 的算法更高效（这正是单线程 Disruptor 设计的理由之一，来源 S9）。
- 【二手】"GC-free / 零分配"编码是该流派标志；TLAB（Thread-Local Allocation Buffer）提供无锁分配；Epsilon GC（JDK11+）是 no-op，仅当应用确定 GC-free 时用（来源 S9）。

### 8. 尾延迟（Tail Latency，p99/p999）与延迟度量（Gil Tene 视角）
延迟 vs 吞吐量权衡的度量基础。Gil Tene（Azul CTO）是该子领域代表。
- 【一手/概念】Coordinated Omission（协同遗漏）：测量系统无意中与被测系统"协同"，从而漏测离群值——典型场景：闭环压测器等上个请求返回才发下个，系统卡顿 5s 时压测器也停发，结果只记到 1 个坏样本，p99 报 1ms 却完全失真（来源 S10，Tene 提出）。
- 修正：开环负载生成（恒定速率发请求，不管前一个是否完成）。Tene 在 wrk2 中先行实践，后被 Vegeta/autocannon/k6(v0.27+) 采纳（来源 S10）。
- 【一手/转述】Tene 核心论点：真正重要的是大多数用户拿到的——p99, p999, p9999, p100，不是均值（"How NOT to Measure Latency" 演讲，来源 S10）。
- 【一手/名言】"Outliers are the norm"（大规模系统中离群是常态）：磁盘 IO 抖动、上下文切换、cache miss、偶发锁竞争在 1/1000 概率上累积，足够多次试验下必然规律性出现（来源 S10）。
- 工具：HDR Histogram 捕获完整分布（Tene 主推，但他对其普及持悲观态度，来源 S10）。

---

## 关键术语

| 术语 | 含义 | 来源 |
| --- | --- | --- |
| Mechanical Sympathy | 理解硬件以与之协同写软件 | S1 |
| Cache line / 缓存行 | 缓存一致性基本单位，x86 常 64B | S2/S5 |
| False sharing / 伪共享 | 不同线程写同一缓存行内的无关变量导致写竞争 | S2/S5 |
| Cache line padding | 字段间填充使跨线程变量各占独立缓存行 | S5 |
| Ring buffer / 环形缓冲 | Disruptor 核心，预分配有界结构 | S2 |
| Sequencing | Disruptor 用序号+memory barrier 管理并发 | S2 |
| Single Writer Principle | 单一写者拥有某资源全部写权 | S6 |
| Little's Law | 排队论，解释竞争下延迟不可预测 | S6 |
| Natural Batching | 贪婪构批，有数据即开、空/满即收 | S8 |
| Data-Oriented Design (DOD) | 程序本质是数据变换，围绕数据使用模式设计 | S7 |
| AoS / SoA | Array of Structs vs Struct of Arrays（内存布局） | S7（推断为 DOD 常用术语） |
| TTSP (Time To Safepoint) | 线程到达安全点的时间，低延迟关键 | S9 |
| TLAB | Thread-Local Allocation Buffer，无锁分配 | S9 |
| Coordinated Omission | 协同遗漏，闭环压测漏测离群值的度量陷阱 | S10 |
| p99/p999/p9999 | 尾延迟百分位 | S10 |
| HDR Histogram | 高动态范围直方图，完整延迟分布 | S10 |

---

## 核心信念

1. 硬件是真正的平台，软件不是。性能问题的答案在硬件行为里（缓存、内存层级、一致性协议），不在抽象层。【一手 S1/S7】
2. 数据访问模式决定性能。可预测、顺序、缓存友好的内存访问优先。【二手蒸馏 S8 / 一手 S7】
3. 竞争是可扩展性头号敌人。能不共享就不共享；写竞争比读昂贵几个数量级。【一手 S6】
4. 单写者 > 锁。业务逻辑跑单线程，无锁只留给底层基础设施。【一手 S6】
5. 预分配 + 零分配。规避 GC 压力优于调 GC 参数；机制（mechanism）优于框架（framework）。【一手 S2/S9】
6. 度量必须看尾部，且必须正确度量（防协同遗漏）。均值/低百分位会骗人。【一手 S10】
7. 程序的本质是数据变换；理解数据=理解问题。【一手 S7】

---

## 反模式（该流派明确反对）

| 反模式 | 反对者/出处 | 说明 |
| --- | --- | --- |
| 过度抽象 / 围绕"世界模型"建类层级 | Acton【一手 S7】 | 现实相似 ≠ 数据变换相似；Chair 例子 |
| 把软件当平台、忽视底层硬件 | Acton / Thompson【一手 S1/S7】 | "Three Big Lies" 之首 |
| 用通用有界队列做线程间交换 | Disruptor 论文【一手 S2】 | head/tail/size 写竞争、忽空忽满、Java 中产生垃圾 |
| 主流程用锁/条件变量 | Thompson【一手 S6】 | 排队效应致延迟不可预测、限制吞吐 |
| 业务逻辑用 lock-free 算法 | Thompson【一手 S6】 | 极难证明正确，应只用于底层组件 |
| 高对象分配率 / 依赖 GC 兜底 | Thompson【一手 S9】 | 分配率直接决定 GC 频率与停顿 |
| 大量线程 + 频繁 stop-the-world | Thompson【一手 S9】 | 恢复调度压力大；少依赖 STW 更优 |
| 闭环压测报均值/低百分位 | Tene【一手 S10】 | 协同遗漏掩盖真实尾延迟 |
| 代码比数据重要的观念 | Acton【一手 S7】 | "Code is ephemeral and has no real intrinsic value." |

---

## 代表性引用（带出处）

1. 【一手 S1】"I want to try and produce software which does justice to the wonderful achievements of our hardware friends." — Thompson, "Why Mechanical Sympathy?"
2. 【一手 S2】"if two variables are in the same cache line, and they are written to by different threads, then they present the same problems of write contention as if they were a single variable. This is a concept know as 'false sharing'." — Disruptor 论文
3. 【一手 S6】"the single biggest limitation on scalability is having multiple writers contend for any item of data or resource." — Thompson, "Single Writer Principle"
4. 【一手 S6】"this queueing effect (Little's Law) causes latency to become unpredictable and ultimately restricts throughput." — 同上
5. 【一手 S7】"The purpose of all programs, and all parts of those programs, is to transform data from one form to another." — Acton, CppCon 2014
6. 【一手 S7】"If you don't understand the data, you don't understand the problem." — 同上
7. 【一手 S7】"Code is ephemeral and has no real intrinsic value."（Lie #3）— 同上
8. 【一手 S10】"Outliers are the norm."（大规模系统）— Gil Tene（转述自 "How NOT to Measure Latency"）
9. 【二手 S0】关于 Disruptor 命名："The Disruptor framework is just one example of what his mechanical sympathy has created." — Blogger 个人简介

---

## 来源清单

| ID | 标题 / 作者 | 类型 | 可信度 | URL |
| --- | --- | --- | --- | --- |
| S0 | Mechanical Sympathy 博客主页 / Blogger 简介 — Thompson | 一手（本人平台） | 高 | https://mechanical-sympathy.blogspot.com/ |
| S1 | "Why Mechanical Sympathy?" (2011-07) — Thompson | 一手（本人博客） | 高 | https://mechanical-sympathy.blogspot.com/2011/07/why-mechanical-sympathy.html |
| S2 | "Disruptor: High performance alternative to bounded queues" v1.0 (2011-05) — Thompson, Farley, Barker, Gee, Stewart | 一手（原始论文） | 高 | https://lmax-exchange.github.io/disruptor/disruptor.html （PDF: https://lmax-exchange.github.io/disruptor/files/Disruptor-1.0.pdf） |
| S3 | "LMAX Disruptor: Fast Concurrent Ring Buffer" — Evan Jones | 二手（独立评审，含矛盾点） | 中高 | https://www.evanjones.ca/lmax-disruptor.html |
| S4 | "The LMAX Architecture" — Martin Fowler | 二手（权威综述） | 高 | https://martinfowler.com/articles/lmax.html |
| S5 | "False Sharing" (2011-07) + "False Sharing && Java 7" (2011-08) — Thompson | 一手（本人博客，经搜索转述） | 高（原文）/ 中（转述） | https://mechanical-sympathy.blogspot.com/2011/07/false-sharing.html ；https://mechanical-sympathy.blogspot.com/2011/08/false-sharing-java-7.html |
| S6 | "Single Writer Principle" (2011-09) — Thompson | 一手（本人博客） | 高 | https://mechanical-sympathy.blogspot.com/2011/09/single-writer-principle.html |
| S7 | "Data-Oriented Design and C++" — Mike Acton, CppCon 2014 | 一手（本人演讲，含 slides/视频） | 高 | https://www.youtube.com/watch?v=rX0ItVEVjHc （slides: https://github.com/CppCon/CppCon2014/tree/master/Presentations/Data-Oriented%20Design%20and%20C%2B%2B） |
| S8 | "Principles of Mechanical Sympathy" — martinfowler.com | 二手（蒸馏综述） | 高 | https://martinfowler.com/articles/mechanical-sympathy-principles.html |
| S9 | "Java Garbage Collection Distilled" (2013-07) — Thompson | 一手（本人博客 / InfoQ 同步） | 高 | https://mechanical-sympathy.blogspot.com/2013/07/java-garbage-collection-distilled.html ；https://www.infoq.com/articles/Java_Garbage_Collection_Distilled/ |
| S10 | "On Coordinated Omission" (ScyllaDB) + Gil Tene "How NOT to Measure Latency" | 一手概念（Tene 提出）/ 二手转述（ScyllaDB） | 中高 | https://www.scylladb.com/2021/04/22/on-coordinated-omission/ ；视频 https://www.youtube.com/watch?v=lJ8ydIuPFeU |
| S11 | InfoQ 访谈 "Martin Thompson on Low Latency Coding and Mechanical Sympathy" | 一手（本人访谈） | 高 | https://www.infoq.com/interviews/martin-thompson-Low-Latency |

一手来源（S0/S1/S2/S5/S6/S7/S9/S11，及 S10 中 Tene 概念）：约 9 条；总来源 12 条。一手占比 > 65%。

---

## 缺口标注

- S5（False Sharing 两篇）、S6（Smart Batching 段落）部分依赖搜索引擎转述，未逐字读全文原文；padding 具体代码（PaddedAtomicLong）未取原始片段。需要时直接 fetch 博客原文核对。
- Acton "Three Big Lies" 的 2008 原始 CellPerformance 博客未取到一手链接（站点已不稳定），目前经 CppCon 重述 + ACCU 综述（S7 系）转述。
- Gil Tene 与 Martin Thompson 在尾延迟上的关系为弱关联，未找到 Thompson 本人直接大段论述尾延迟的一手文本；尾延迟方法论主要由 Tene 承载。
- 未覆盖：Aeron / SBE（Thompson 后期作品）、Universal Scalability Law（Neil Gunther，与单写者论证相关但 Thompson 该文未直接引用）——若 Skill 需要可补查。
