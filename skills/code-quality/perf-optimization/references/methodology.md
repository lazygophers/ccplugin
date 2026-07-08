# 跨栈核心方法论(详解)

七条方法论各自的证据、应用、局限。每条都在 ≥2 个独立流派中复现,是优化任何系统的通用信条。SKILL.md 的速查表是这里的浓缩。

## 方法论 1: 测量先于优化,禁止靠猜
**核心**:在证明瓶颈位置之前,不要动手优化。
**证据**:Rob Pike 规则 1-2「You can't tell where a program is going to spend its time... Measure.」(Notes on Programming in C, 1989);Brendan Gregg 把凭直觉调优命名为反方法论,2013 Velocity 演讲题为《Stop the Guessing》。跨算法/系统/前端三域复现。
**应用**:任何"我觉得这里慢"的论断,先问"测了吗?数据呢?"
**局限**:探索性原型期、一次性脚本可放宽;但凡进入生产路径就适用。

## 方法论 2: 瓶颈思维 —— 优化收益被主导成本锁死(Amdahl 定律)
**核心**:在 5 处各砍 5% 几乎不改变用户体验;先猎杀单一主导成本。
**证据**:Amdahl 定律(1967),总加速 = 1/((1-p)+p/s),s→∞ 上限 = 1/(1-p)——优化占比 p 小的部分,收益被锁死。Gregg 的延迟分析、80-20 法则同源。
**应用**:拿到 profiling 先看最宽的火焰图平顶 / 占比最大的那一项,而非到处微调。
**局限**:主导成本消除后,次要成本会浮现为新主导,需迭代重测。

## 方法论 3: 延迟是分布,要看尾部不看均值
**核心**:p99/p999 才是系统真实运行上限,均值会骗人。
**证据**:Gil Tene「Outliers are the norm」;Google SRE 四黄金信号以 Latency 分布为核心;扇出(fan-out)系统里请求依赖多服务,尾延迟决定整体。
**应用**:报告性能必带分位数;请求扇出越多,越要盯尾部。
**陷阱**:协调遗漏(Coordinated Omission)——闭环压测器在系统卡顿时也停发请求,导致 p99 被严重低估。改用开环负载生成(wrk2/k6),用 HDR Histogram 抓完整分布。详见 `benchmarking.md`。

## 方法论 4: 过早优化纪律 —— 只优化已识别的关键 3%
**核心**:不为非关键路径瞎操心,但绝不放过关键 3%。
**证据**:Knuth 1974 原文「We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. **Yet we should not pass up our opportunities in that critical 3%** ... but only after that code has been identified.」(ACM Computing Surveys 6:4)。关键是"先识别再优化",不是"永不优化"。
**应用**:听到"过早优化是万恶之源"当挡箭牌时,反问"这是不是那关键 3%?你怎么知道它不是?"
**局限**:这句话被双向滥用,既被用来拒绝一切优化,也被忽略导致过早劣化。详见 `tensions.md` 张力 1/2。

## 方法论 5: 机制同理心 —— 数据访问模式决定性能
**核心**:理解硬件(缓存、内存层级、一致性协议)来写与之协同的代码;数据布局 > 算法巧思。
**证据**:Martin Thompson「为硬件写软件」;Mike Acton「程序的本质是数据变换,不理解数据就不理解问题」(CppCon 2014);Rob Pike 规则 5「Data dominates」。
**应用**:性能关键路径上,先看数据怎么排布、访问是否顺序、有无跨线程写竞争——再谈算法。
**局限**:仅对性能关键的热点值得;非热点上贴硬件设计是过度工程。详见 `tensions.md` 张力 4。

## 方法论 6: 科学方法循环 —— 假设→测量→验证→迭代
**核心**:把假设写成「If X, then we'd expect Y」,做实验确认或否定,使分析可复现。
**证据**:Gregg 的 Scientific Method(LISA 2012);Jon Bentley《Writing Efficient Programs》对同一代码逐条应用规则、逐版迭代到 1+ 数量级提升。
**应用**:优化是实验不是赌博。每次只改一个变量,改完回到 baseline 重测,确认收益为真且无回归。
**局限**:要求可复现的测量环境,生产环境噪声大时需多次采样。

## 方法论 7: 系统级 trade-off 是耦合的,不是对立的
**核心**:延迟与吞吐由 Little 定律耦合(并发 = 吞吐 × 延迟);好设计是控制 trade-off 而非消除。
**证据**:Little 定律 L=λW(1961),不受分布影响的普适关系;空间换时间(缓存/查表)、可读性 vs 性能都是经典权衡。
**应用**:有人说"既要低延迟又要高吞吐"时,用 Little 定律说明二者关系;系统接近容量时延迟必然上升。
**局限**:稳态关系,突发流量/排队瞬态需另行建模。
