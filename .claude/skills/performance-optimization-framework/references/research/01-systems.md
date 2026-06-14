# 系统/后端性能优化流派调研 — Brendan Gregg 方法论

> 调研范围：USE 方法、火焰图、eBPF/动态追踪、科学方法论、USE vs RED、反模式、核心信念。
> 来源策略：一手优先（本人书籍/博客 brendangregg.com/会议演讲），二手仅作补充。
> 可信度标记：一手 = 本人网站/书/演讲；二手 = 第三方转述；推测 = 调研者推断。
> 标注约定：「本人说的」/「他人总结的」/「我推断的」分别标注。

## 信息充足性

所有验收维度均覆盖，未触发「信息不足」。一手来源占比 > 50%（11 条来源中 8 条来自 brendangregg.com）。RED 方法部分一手来源为 Tom Wilkie（RED 发明人）本人转述，但通过二手媒体获取，标注为「二手转述一手观点」。

---

## 核心方法论

### 1. USE 方法（Utilization / Saturation / Errors）

定位：系统资源瓶颈定位框架，性能调查的**第一步**（fast, high-value first step），用于快速发现系统性瓶颈。

核心规则（本人说的，一手）：
> "For every resource, check utilization, saturation, and errors."
> 对每个资源，检查利用率、饱和度、错误。
- 来源：https://www.brendangregg.com/usemethod.html （一手）

三个指标的精确定义（本人说的，一手，逐字）：
- **Utilization**: "the average time that the resource was busy servicing work"（资源忙于处理工作的平均时间）
- **Saturation**: "the degree to which the resource has extra work which it can't service, often queued"（资源有无法处理、通常排队的额外工作的程度）
- **Errors**: "the count of error events"（错误事件计数）
- 来源：https://www.brendangregg.com/usemethod.html （一手）

指标的典型表达方式（本人说的，一手）：
- Utilization：时间区间内的百分比，如「一块磁盘运行在 90% 利用率」
- Saturation：队列长度，如「CPU 平均运行队列长度为 4」
- Errors：标量计数
- 来源：https://www.brendangregg.com/usemethod.html （一手）

利用率定义的歧义（本人说的，一手）：存在两种定义。一种是上面的「忙碌时间占比」；另一种描述「资源被占用的比例」，此定义下 100% 利用率 = 无法再接受任何工作（与「忙碌」定义不同——磁盘 90% 忙仍可接受更多请求，但 100% 容量占用则不能）。
- 来源：https://www.brendangregg.com/usemethod.html （一手）
- 注：这是流派内部的术语张力，按要求保留不调和。

应用步骤（本人说的，一手）：
1. 枚举硬件资源：CPU、主存、网络接口、存储设备、控制器、互连总线。
2. 找到/绘制服务器功能框图（functional diagram），分析数据路径上的每个组件。
3. 软件资源同样适用：互斥锁、线程池、进程/线程容量、文件描述符容量。
4. 为每个资源构造 U/S/E 检查清单，发现问题后再用其他方法深入。
- 来源：https://www.brendangregg.com/usemethod.html （一手）

价值主张（本人说的，一手）：
> 「solves about 80% of server issues with 5% of the effort」（用 5% 的努力解决约 80% 的服务器问题）
- 来源：https://www.brendangregg.com/usemethod.html （一手）

副作用价值（本人说的，一手）：USE 会暴露「缺失的指标」——当前工具集没提供的度量。这些是「已知的未知」（known unknowns），远好于「未知的未知」。由此可指导安装/开发新工具。
- 来源：https://www.brendangregg.com/usemethod.html （一手）

OS 专属检查清单（本人维护，一手）：Linux / Solaris / SmartOS / macOS 各有一份 checklist。
- Linux: https://www.brendangregg.com/USEmethod/use-linux.html （一手）

### 2. 火焰图（Flame Graphs）

定义（本人说的，一手，逐字）：
> "a visualization of hierarchical data that I created to visualize stack traces of profiled software so that the most frequent code-paths can be identified quickly and accurately"
> （我创建的一种层级数据可视化，用于可视化被剖析软件的栈轨迹，从而快速准确地识别最频繁的代码路径）
- 来源：https://www.brendangregg.com/flamegraphs.html （一手）

发明动机（本人说的，一手）：
- 2011 年，调查一个 MySQL 性能问题时发明，需要快速且深入理解 CPU 使用情况。
- 常规 profiler/tracer 产生「成墙的文本」（walls of text），数千行难以消化。
- 此前要理解一个复杂 profile 可能要花数小时读数百页输出；火焰图把它变成几秒——「只需找最宽的矩形」。
- 来源：https://www.brendangregg.com/flamegraphs.html （一手）

技术演进决策（本人说的，一手，逐字）：
> "I switched to timed sampling (profiling) to solve the overhead problem, but since the function flow is no longer known (sampling has gaps) I ditched time on the x-axis and reordered samples to maximize frame merging."
> （我改用定时采样以解决开销问题；但由于函数流程不再已知（采样有间隙），我放弃了 x 轴上的时间维度，重排样本以最大化帧合并。）
- 来源：https://www.brendangregg.com/flamegraphs.html （一手）
- 注：建立在前人工作之上——Neelakanth Nadgir 的时序栈可视化，又受 Roch Bourbonnais 的 CallStackAnalyzer 和 Jan Boerhout 的 vftrace 启发。前人方案两大问题：函数追踪开销太高扰动目标，且跨多秒时可视化太密集无法阅读。

如何阅读（本人说的，一手）：
- **Y 轴**：栈深度，从底部 0 向上计数；每个矩形是一个栈帧，祖先在下、被调用在上。
- **X 轴**：栈样本总体，**按字母排序**（不是时间），目的是最大化帧合并、呈现整体画面。从左到右的顺序不重要。
- **颜色**：随机，仅用于区分相邻帧，颜色本身无意义（暖色调隐喻 CPU 为何「热/忙」）。
- **宽度**：「the wider a frame appears, the more often it was present in the stacks」——帧越宽，在栈中出现越频繁，直接表示消耗的 CPU 时间/资源越多。
- **技巧**：自底向上找最宽的帧，关注「火焰」中的分叉（不同代码路径）。
- 来源：https://www.brendangregg.com/flamegraphs.html ；https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html （一手）

采纳与影响（本人说的，一手）：已成 CPU 剖析标准；催生 5 家创业公司，被 30+ 性能分析产品采纳，80+ 实现，覆盖多种语言。开源工具：github.com/brendangregg/FlameGraph。
- 来源：https://www.brendangregg.com/flamegraphs.html （一手）

### 3. eBPF / BPF / 动态追踪 / off-CPU 分析

BPF 类比（本人说的，一手，逐字）：
> "In some ways, eBPF does to the kernel what JavaScript does to websites: it allows all sorts of new applications to be created."
> （某种意义上，eBPF 之于内核就像 JavaScript 之于网站：它允许创建各种新应用。）
- 来源：https://www.brendangregg.com/ebpf.html （一手）

「超能力」（superpowers）框架（本人说的，一手）：
- 反复出现的主题。演讲标题：USENIX LISA 2016「Linux 4.x Tracing Tools: Using BPF Superpowers」、Velocity 2017「Performance Analysis Superpowers with Linux eBPF」、博客「Linux BPF Superpowers」（2016）。
- 核心能力：动态插桩（dynamic instrumentation / dynamic tracing）是一种「超能力」——可在运行中的二进制里追踪**任意软件函数**，无需重启，能查到几乎任何问题的根因。
- 来源：https://www.brendangregg.com/blog/2016-03-05/linux-bpf-superpowers.html （一手）

动态 vs 静态追踪（本人说的，一手）：
- 动态：kprobes（内核）、uprobes（用户态）——可追踪任意函数。
- 静态：tracepoints、USDT——事件点硬编码、成为稳定 API。
- 建议：**尽量优先静态插桩**，因为动态函数不是稳定 API，会随软件版本变化。
- 来源：https://www.brendangregg.com/blog/2019-08-19/bpftrace.html （一手）

前端工具选型（本人说的，一手）：BCC 用于复杂工具/守护进程；bpftrace 用于一行命令和短脚本。bpftrace 是入门 BPF 可观测性的最佳途径。
- 来源：https://www.brendangregg.com/blog/2019-08-19/bpftrace.html （一手）

off-CPU 分析（本人说的，一手）：
- 定义为「分析阻塞时间的方法论，与 CPU 分析互补」（complimentary to CPU analysis）。
- 衍生技术：Off-CPU Flame Graph、Wakeup / Off-Wake Profiling、「Who is waking the waker?」（唤醒链图原型，2016）。
- 推断（我推断的）：off-CPU 是对「on-CPU 火焰图只看消耗 CPU 的代码」的盲区补全——线程等待 I/O/锁/调度的时间在 on-CPU 图上不可见。
- 来源：https://www.brendangregg.com/offcpuanalysis.html （索引于 https://www.brendangregg.com/overview.html ，一手）

### 4. 性能分析方法论全集（10 种方法与反方法）

来源：USENIX LISA 2012 演讲「Performance Analysis Methodology」+ ACMQ 文章「Thinking Methodically about Performance」（本人，一手）。
- https://www.brendangregg.com/Slides/LISA2012_methodologies.pdf （一手）
- https://www.brendangregg.com/blog/2012-12-13/usenix-lisa-2012-performance-analysis-methodology.html （一手）

正向方法论：
1. **Ad Hoc Checklist Method**：跑预设的条件检查清单。
2. **Problem Statement Method**：先问清问题——开场问「What makes you think there is a performance problem?」。
3. **Scientific Method**：问题→假设→预测→测试→分析。
4. **Workload Characterization Method**：刻画负载的 who/why/what/how。
5. **Drill-Down Analysis Method**：从高层逐级下钻到低层细节。
6. **Latency Analysis Method**：测量并分解操作耗时为各组成部分。
7. **USE Method**：每个资源查 U/S/E。
8. **Stack Profile Method**：剖析并系统研究线程栈（火焰图的方法论母体）。
- 此外 usemethod.html 提到 Cary Millsap 的 **Method R**（基于延迟的方法）作为互补。

---

## USE vs RED 方法论对比

RED 方法发明人：**Tom Wilkie**（非 Gregg），2015 年在 Weaveworks 提出，首次公开于伦敦 Prometheus meetup。源自 Google SRE 的「Four Golden Signals」（Latency/Traffic/Errors/Saturation）。
- 来源：https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ （一手，Wilkie 所在公司）

RED = 每个**服务**测三个指标：
- **Rate**：每秒请求数
- **Errors**：失败请求数
- **Duration**：处理请求耗时

核心区别（他人总结的 + Wilkie 本人转述）：
- USE 问「我的基础设施健康吗？」（面向硬件/资源）；RED 问「我的服务在很好地服务用户吗？」（面向请求驱动型服务）。
- Wilkie 本人观点（二手转述一手）：
  > "The USE Method doesn't really apply to services; it applies to hardware, network disks, things like this. We really wanted a microservices-oriented monitoring philosophy, so we came up with the RED Method."
- Wilkie 指出 USE 在软件上的痛点：内存饱和度难测、I/O 与内存带宽错误计数难拿——「Linux, it turns out, is really bad at exposing error counts.」
- 来源：https://thenewstack.io/monitoring-microservices-red-method/ （二手，转述 Wilkie 原话）

互补而非替代（他人总结的）：RED 用于 API/网关/服务网格；USE 用于 CPU/内存/磁盘等基础设施资源。RED 指标显示响应变慢→USE 指标可能揭示某 DB 服务器 CPU 饱和，直接指向根因。
- 来源：https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ （一手）；https://www.infoworld.com/article/2270578/the-red-method-a-new-strategy-for-monitoring-microservices.html （二手）

矛盾点（保留不调和）：
- Gregg 的 USE 把 Errors 当作核心三要素之一，且声称解决 80% 问题；Wilkie 却说 USE 的 errors 在软件层「Linux 很难暴露」，因此另起 RED。两人对「Errors 是否好测」存在事实层面分歧。

---

## 核心术语

| 术语 | 含义 | 出处可信度 |
| --- | --- | --- |
| USE Method | Utilization/Saturation/Errors，资源瓶颈定位 | 一手 |
| Flame Graph | 栈轨迹层级可视化，找最宽帧 | 一手 |
| Off-CPU Analysis | 分析阻塞/等待时间，与 on-CPU 互补 | 一手 |
| eBPF / BPF | 内核内可编程执行引擎，可观测性「超能力」 | 一手 |
| Dynamic tracing | kprobes/uprobes，运行时追踪任意函数 | 一手 |
| Static tracing | tracepoints/USDT，硬编码稳定 API | 一手 |
| Workload Characterization | 刻画负载 who/why/what/how | 一手 |
| Drill-Down Analysis | 从高层下钻到低层 | 一手 |
| Latency Analysis | 分解操作耗时 | 一手 |
| Known unknowns | USE 暴露的缺失指标 | 一手 |
| RED Method | Rate/Errors/Duration，面向服务（Tom Wilkie） | 一手（Wilkie 侧） |
| Four Golden Signals | Latency/Traffic/Errors/Saturation（Google SRE） | 二手 |

---

## 核心信念（出现 ≥ 3 次的反复主张）

1. **「不要猜，要测」/「停止猜测」（Don't guess, measure）**
   - Velocity 2013 演讲直接命名为「Stop the Guessing: Performance Methodologies for Production Systems」。
   - 科学方法论（假设→预测→测试）被列为正向方法。
   - 反模式集合（streetlight / random change / blame-someone-else）本质都是「不测就行动」。
   - 来源：https://www.brendangregg.com/Slides/VelocityStopTheGuessing2013.pdf ；LISA2012_methodologies.pdf （一手）
   - 判定：本人说的，跨多个演讲反复出现，≥3 次。

2. **「先有方法论，工具只是回答方法论提出的问题」**
   - 反复强调方法论先行：USE/TSA/workload characterization 等「提出问题」，工具负责「回答」。
   - 「方法论是工具箱里的一件工具，是更大方法论工具箱的一部分」。
   - 来源：usemethod.html ；LISA2012_methodologies.pdf ；EuroBSDcon2017 System Methodology slides（一手）
   - 判定：本人说的，≥3 次。

3. **「快速完整体检优先」（completeness over depth-first，先广度后深度）**
   - USE 设计为「快速完整检查」，先枚举所有资源做一遍 U/S/E，而非一头扎进单个组件。
   - drill-down 也是从高层整体开始。
   - 火焰图同理——先看整体「big picture」再找宽帧。
   - 来源：usemethod.html ；flamegraphs.html （一手）
   - 判定：本人说的 + 我推断的（跨方法论的统一模式），≥3 次结构性出现。

4. **「让不可见可见」（make the invisible visible）**
   - 火焰图把成墙文本变成可秒读图像；off-CPU 把等待时间显式化；eBPF 把内核内部追踪能力交给用户；USE 暴露 known unknowns。
   - 来源：flamegraphs.html ；ebpf.html ；offcpuanalysis 索引（一手）
   - 判定：我推断的（贯穿其工具创造的统一动机），≥3 个独立产物体现。

---

## 反模式（Anti-Methods）

来源：LISA 2012 methodologies + ACMQ「Thinking Methodically about Performance」（本人，一手）。

1. **Streetlight Anti-Method（路灯反方法）**
   - 典出「醉汉在路灯下找钥匙」寓言：不是因为钥匙丢在那，而是因为那里有光。
   - 性能上：用手边熟悉/网上随便找/随机选的工具与指标，而非真正能定位问题的工具。
   - 原话（一手）：挑工具是「familiar / found on the Internet / found at random」。
   - 来源：https://www.brendangregg.com/Slides/LISA2012_methodologies.pdf （一手）

2. **Random Change Anti-Method（随机改动反方法）**
   - 随机改 tunable/配置/参数看性能是否变好——即靠猜而非测量推理瓶颈。
   - 来源：LISA2012_methodologies.pdf （一手）；二手转述 https://www.brendangregg.com/blog/2012-12-13/usenix-lisa-2012-performance-analysis-methodology.html

3. **Blame-Someone-Else Anti-Method（甩锅反方法）**
   - 把问题推给自己不负责的组件，无证据地让别的团队去查。
   - 来源：LISA2012_methodologies.pdf （一手）

延伸反模式（我推断的，基于其反复批判的对象）：凭直觉调优（intuition-based tuning）、过早优化未度量、只看 on-CPU 而忽视 off-CPU 等待时间。

---

## 代表性引用（带出处）

1. 「For every resource, check utilization, saturation, and errors.」
   — usemethod.html （一手，本人）

2. 「solves about 80% of server issues with 5% of the effort」
   — usemethod.html （一手，本人，谈 USE 价值）

3. 「a visualization of hierarchical data that I created to visualize stack traces of profiled software so that the most frequent code-paths can be identified quickly and accurately」
   — flamegraphs.html （一手，本人，火焰图定义）

4. 「the wider a frame appears, the more often it was present in the stacks」
   — flamegraphs.html （一手，本人，阅读法核心）

5. 「In some ways, eBPF does to the kernel what JavaScript does to websites: it allows all sorts of new applications to be created.」
   — ebpf.html （一手，本人）

6. 「The USE Method doesn't really apply to services; it applies to hardware, network disks... We really wanted a microservices-oriented monitoring philosophy, so we came up with the RED Method.」
   — Tom Wilkie，转载于 thenewstack.io （二手转述一手观点）

7. 「Linux, it turns out, is really bad at exposing error counts.」
   — Tom Wilkie，同上（二手转述一手观点）

8. 「Stop the Guessing」（演讲标题，体现「不要猜要测」信念）
   — VelocityStopTheGuessing2013.pdf （一手，本人）

---

## 来源清单

一手（brendangregg.com 本人）：
1. https://www.brendangregg.com/usemethod.html — USE 方法权威页 【一手】
2. https://www.brendangregg.com/USEmethod/use-linux.html — Linux USE 检查清单 【一手】
3. https://www.brendangregg.com/flamegraphs.html — 火焰图主页（定义/阅读/起源）【一手】
4. https://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html — CPU 火焰图 【一手】
5. https://www.brendangregg.com/ebpf.html — Linux eBPF Tracing Tools 【一手】
6. https://www.brendangregg.com/blog/2016-03-05/linux-bpf-superpowers.html — BPF Superpowers 【一手】
7. https://www.brendangregg.com/blog/2019-08-19/bpftrace.html — bpftrace 介绍（动态 vs 静态）【一手】
8. https://www.brendangregg.com/Slides/LISA2012_methodologies.pdf — 10 方法/反方法演讲 【一手】
9. https://www.brendangregg.com/blog/2012-12-13/usenix-lisa-2012-performance-analysis-methodology.html — 同上博客版 【一手】
10. https://www.brendangregg.com/Slides/VelocityStopTheGuessing2013.pdf — Stop the Guessing 演讲 【一手】

一手（Tom Wilkie / Grafana 侧，RED 发明方）：
11. https://grafana.com/blog/the-red-method-how-to-instrument-your-services/ — RED 方法官方 【一手（RED 侧）】

二手（补充/转述）：
12. https://thenewstack.io/monitoring-microservices-red-method/ — 转述 Wilkie 原话 【二手】
13. https://www.infoworld.com/article/2270578/the-red-method-a-new-strategy-for-monitoring-microservices.html — RED vs USE 【二手】

未直接抓取但本人索引存在（可后续补一手细读）：
- https://www.brendangregg.com/overview.html — 含 off-CPU analysis、wakeup profiling 等索引 【一手】
- ACMQ「Thinking Methodically about Performance」「The Flame Graph」（2016）— 论文，未抓全文 【一手，缺口】
- 书籍《Systems Performance》《BPF Performance Tools》— 未取原文页码 【一手，缺口】

### 缺口说明
- 两本核心书籍未取到逐页原文（仅取到 brendangregg.com 上的书籍介绍页转述），书中可能有更精炼的方法论表述（如 Systems Performance 中的「60-second checklist」）未覆盖。
- ACMQ 两篇论文全文未抓取，引用以网站/演讲为准。
- 「核心信念」第 3、4 条部分为调研者跨产物归纳（标注「我推断的」），非本人逐字原话。
