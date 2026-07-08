# 内在张力(详解)

性能优化领域没有统一教条。下列分歧是判断力的来源——遇到具体场景要权衡,不要背诵口号。标注区分「真实公开争论」与「归纳的张力」。

## 张力 1: 「过早优化是万恶之源」—— 被滥用 vs 原意
被截成口号论证"性能根本不该提前考虑",甚至"永远别优化"。但 Knuth 原文在**捍卫**合理效率追求,只反对非关键路径瞎操心,且同篇直接抨击了反向极端:"ignoring efficiency in the small ... is simply an overreaction to the abuses ... by penny-wise-and-pound-foolish programmers"。被丢掉的关键限定词是「97%」「关键 3%」「先识别再优化」。**真实争论**(HN/多篇考据还原原文)。

## 张力 2: 过早优化 vs 过早劣化(premature pessimization)
Sutter & Alexandrescu(C++ Coding Standards Item 9):"不要过早优化"**不等于**可以随手写低效代码;在复杂度和可读性都不变时,高效写法应自然流出(该传引用就别传值、用初始化列表而非构造体内赋值)。两者构成**双侧约束**:既不为臆想优化,也不为显摆"不优化"而劣化。库开发场景天平偏向效率(调用上下文未知)。**真实**(书中明确成文)。

## 张力 3: 可维护性优先 vs 数据导向/性能优先(OOP vs DOD)
**Uncle Bob**:"省程序员的周期比省机器周期更经济",多数软件用不到 1% CPU,先为可读性写。
**Mike Acton / Casey Muratori**:程序本质是数据变换,Clean Code 的多态/小函数拆分能让程序慢一个数量级("Clean Code, Horrible Performance")。
**真实**(GitHub unclebob/cmuratori-discussion 公开逐条往返 + SE Radio 577)。收敛点:Bob 承认性能意识该更突出,Casey 承认非关键系统里生产力收益成立。

## 张力 4: 自上而下找瓶颈 vs 自下而上贴硬件
**Gregg**:先用方法论问"该问系统什么问题",再抓工具,天然防"瞎猜微优化"。
**Thompson/Acton**:某些性能必须在架构期贴硬件设计,事后 profiling 救不回。
**部分真实部分推断**:两人立场各自真实,但无公开互辩,实践中常互补(先测量定位热点,再贴硬件重写热点)。

## 张力 5: 微基准 vs 真实负载
微基准像单元测试快速对比候选实现;但 JVM/硬件的自适应优化会扭曲隔离测量,"看着可信但误导"。根因是"小程序邀请了真实负载里不会发生的过度优化"。准确的前提是忠实复现生产执行条件——而这恰是微基准最难做到的。**真实**(JMH 陷阱是公认工程事实)。具体防优化手段见 `benchmarking.md`。

## 关键引用

> "Premature optimization is the root of all evil. **Yet we should not pass up our opportunities in that critical 3%** ... but only after that code has been identified." —— Knuth, 1974

> "Don't guess, measure." —— Brendan Gregg, 《Systems Performance》

> "The purpose of all programs ... is to transform data from one form to another." —— Mike Acton, CppCon 2014

> "Outliers are the norm." —— Gil Tene
