# 跨语言微基准陷阱与正确姿势(非 JVM)

> 配套 04-methodology.md(JVM/JMH 视角)。本文只补 Go / Rust / C++,不重复 JMH 的 DCE/常量折叠/JIT 预热/Blackhole/伪共享条目。

## 跨语言共性结论

四条规律在所有编译型/JIT 语言里都成立,JMH 的 `Blackhole` 只是其中第一条的一种实现:

1. **结果必须被消费,否则优化器合法删掉它。** 一个计算如果其结果没有任何可观察的副作用(没被存储、没被读取、没参与后续依赖),编译器在 `-O2`/JIT 优化下删掉它是完全合法的——这就是死代码消除(DCE)。微基准里"测了个寂寞"的根因几乎都是这个。各语言给出的防御手段本质相同:制造一个优化器无法证明无用的"汇点(sink)"——Go 包级变量 / `b.Loop()` 自动 KeepAlive,Rust `black_box`,C++ `DoNotOptimize`。

2. **输入也要保护,否则常量折叠绕过你。** 只保护输出不够。若被测函数的输入是编译期常量,编译器会在编译期算出结果(常量传播 / 常量折叠),你测的就成了"读一个常量"。必须让优化器把输入也当成运行期未知值。这点在 C++ Google Benchmark 里尤其致命(见下)。

3. **预热到稳态再测。** 冷缓存、JIT 未编译、CPU 频率未爬升(DVFS)都会污染前几次测量。Go 用 `b.N` 自适应放大迭代次数摊薄;Rust criterion 有显式 warm-up 阶段;C++ 通常靠足够大的迭代数。

4. **测的是分布而非单点;扣除测量开销。** 单次计时受调度、缓存、中断干扰极大。criterion 用 bootstrap 重采样给出置信区间与离群点分类;Go 跑足够多迭代取 ns/op 均值;都需把 setup/cleanup 排除在计时窗口外(`ResetTimer`/`StopTimer` 或 `b.Loop()` 自动处理)。

---

## Go

### `testing.B` 与 `b.N` 自适应迭代

传统写法把被测代码跑 `b.N` 次。框架会**多次调用**同一 benchmark 函数,每次调大 `b.N`,直到单次运行时间长到足以可靠计时。官方原文:

> "the benchmark function must run the target code b.N times. The benchmark function is called multiple times with b.N adjusted until the benchmark function lasts long enough to be timed reliably. This also means any setup done before the loop may be run several times."(pkg.go.dev/testing,一手)

副作用:**循环前的 setup 可能被重复执行多次**——这是 `b.N` 风格的固有坑,需用 `b.ResetTimer()` 把 setup 排除出计时窗口。

### 为什么需要包级变量 / sink 防 DCE

`b.N` 风格下,若被测函数结果未被消费,编译器(尤其内联后)会把整个调用判定为死代码删掉,得到亚纳秒的假结果。Go 核心贡献者 Dave Cheney 的经典指引(一手作者博客):

> "any benchmark should be careful to avoid compiler optimisations eliminating the function under test and artificially lowering the run time of the benchmark."
> 双重防御:"always record the result of Fib to prevent the compiler eliminating the function call" + "always store the result to a package level variable so the compiler cannot eliminate the Benchmark itself."

标准 sink 模式:

```go
var result int // 包级变量,优化器无法证明无用

func BenchmarkFibComplete(b *testing.B) {
    var r int
    for n := 0; n < b.N; n++ {
        r = Fib(10)  // 先存到局部
    }
    result = r        // 再写回包级 sink
}
```

### Go 1.24 `testing.B.Loop()`(`for b.Loop()`)解决了什么

新写法把"防 DCE + 自动管迭代 + 自动管计时"一并解决,官方推荐新基准一律用它。官方文档原文(一手):

> "Within the body of a 'for b.Loop() { ... }' loop, arguments to and results from function calls and assigned variables within the loop are kept alive, preventing the compiler from fully optimizing away the loop body. Currently, this is implemented as a compiler transformation that wraps such variables with a runtime.KeepAlive intrinsic call. This applies only to statements syntactically between the curly braces of the loop, and the loop condition must be written exactly as 'b.Loop()'."

它解决的三件事(Go 官方博客 testing-b-loop,一手):

- **防 DCE**:编译器识别 `b.Loop()` 作为循环条件,禁止把循环体内联消除。Go 1.24 实现方式是"disallowing inlining into the body of such a loop"。博客举例:旧写法测 `isCond` 可能跑出亚纳秒,因为"this benchmark doesn't measure isCond at all; it measures how long it takes to do nothing"。
- **自动计时**:"The b.ResetTimer at the loop's start and b.StopTimer at its end are integrated into testing.B.Loop"——首次调用自动重置计时器(setup 不计入),返回 false 时自动停表(cleanup 不计入)。
- **单次调用**:`b.Loop()` 只需调用 benchmark 函数一次跑到时间阈值,而非 `b.N` 那样反复 ramp,避免 setup 重跑,也避免误依赖迭代序号。

`b.Loop()` 返回 false 后,`b.N` 仍含总迭代数,可用于算其他平均指标。

### `b.ResetTimer` / `b.ReportAllocs`

- `b.ResetTimer()`:归零已计时间与内存分配计数器,不影响计时器开关状态。用于排除 setup。
- `b.StopTimer()` / `b.StartTimer()`:暂停/恢复计时,排除循环内的 setup/cleanup。
- `b.ReportAllocs()`:为该 benchmark 开启 malloc 统计(等价 `-benchmem` 但只作用于此函数),报告 allocs/op、B/op。
- 来源:pkg.go.dev/testing(一手)。

---

## Rust

### `std::hint::black_box`(及历史上的 `test::black_box`)

`black_box<T>(dummy: T) -> T` 是个恒等函数,但**提示编译器对它的行为做最悲观假设**。历史上这能力只在 nightly 的 `test` crate(`test::black_box`)里,后来稳定进 `std::hint::black_box`,任何 stable Rust 都能用。官方文档原文(一手,doc.rust-lang.org):

> "An identity function that hints to the compiler to be maximally pessimistic about what black_box could do."
> "a Rust compiler is encouraged to assume that black_box can use dummy in any possible valid way that Rust code is allowed to without introducing undefined behavior in the calling code."

它干两件事(对应共性结论 1+2):

> 1. "It prevents the compiler from making optimizations related to the value returned by black_box"(保护输出)
> 2. "It forces the value passed to black_box to be calculated, even if the return value of black_box is unused"(强制求值,即保护输入/防止被测计算被折叠掉)

**关键局限**(必须照搬进 Skill,否则误导用户):

> "black_box is only (and can only be) provided on a 'best-effort' basis. The extent to which it can block optimisations may vary depending upon the platform and code-gen backend used. Programs cannot rely on black_box for correctness... it must not be relied upon to control critical program behavior. This also means that this function does not offer any guarantees for cryptographic or security purposes."
> "During constant evaluation, black_box is treated as a no-op."

即:`black_box` 是尽力而为的优化屏障,不是常量时间密码学的保证手段,也不能在 const eval 阶段起作用。

### criterion crate 与其统计学方法

criterion 是 Rust 事实标准的统计型基准框架。它在 `bench_with_input` 等 API 里**自动**把输入过一遍 `black_box`,用户无需手动调用(bheisler.github.io/criterion.rs,一手):

> "This is convenient in that it automatically passes the input through a black_box so that you don't need to call that directly."

统计学方法(对应共性结论 3+4,来源 criterion.rs analysis 页,一手):

- **Warm-up(预热)**:反复执行被测例程"to fill the CPU and OS caches and (if applicable) give the JIT time to compile the code"。迭代呈指数放大——跑 1 次、2 次、4 次……直到累计执行时间超过配置的 warm-up 时间。
- **Sampling(采样)**:采集多个 sample,迭代数按 `[d, 2d, 3d, ..., Nd]` 线性递增,d 由 warm-up 估算。每 sample 含一至多次迭代,(结束-开始)/迭代数 = 单次迭代时间估计。
- **Outlier detection(离群点检测)**:改良 Tukey 法。低于 `Q1 - 1.5×IQR` 或高于 `Q3 + 1.5×IQR` 标记为离群;超出 `Q1 - 3×IQR` / `Q3 + 3×IQR` 标为 severe(严重)离群。离群点保留在数据集中继续分析(用于提示噪声而非剔除)。
- **Resampling(重采样)**:用 bootstrap 样本给斜率估计造置信区间,导出 mean / std dev / median / MAD 的分布。
- **Comparison(回归对比)**:对 bootstrap 样本做 T 检验,算差异由偶然导致的概率,带可配置噪声阈值(如 ±1%)——这是 criterion 能判"这次改动到底有没有变快"的基础。

---

## C++

### `-O2`/`-O3` 下的 DCE 与常量传播

C++ 编译器在 `-O2`/`-O3` 默认开启死代码消除与常量折叠/常量传播。微基准里:结果没被消费 → 整段计算被删;输入是编译期常量 → 结果在编译期算好,运行期只剩读常量。两者叠加,裸 `for` 循环测出来的常是空气。

### Google Benchmark 的 `DoNotOptimize()` 与 `ClobberMemory()`

`benchmark::DoNotOptimize(<expr>)`:强制 `<expr>` 的**结果**落到内存或寄存器,对 GNU 编译器还充当全局内存的读写屏障。官方文档原文(一手,google.github.io/benchmark):

> "DoNotOptimize(<expr>) forces the result of <expr> to be stored in either memory or a register."

**关键陷阱**——它只保护结果,不保护 `<expr>` 本身:

> "DoNotOptimize(<expr>) does not prevent optimizations on <expr> in any way."

官方反例:`while (...) DoNotOptimize(foo(0));` 会被优化成 `DoNotOptimize(42)`(因为 `foo(0)` 是常量表达式)。官方推荐先把结果物化到局部变量再传:

```cpp
while (...) {
  auto result = foo(0);   // 物化
  DoNotOptimize(result);
}
```

更进一步(对应共性结论 2):**要测加法本身,必须连输入一起 `DoNotOptimize`**,否则 `10 + 20` 被折叠成 `30`,你测的成了 `DoNotOptimize(30)`。即对 `a`、`b` 也调 `DoNotOptimize`,逼编译器把它们当未知值(studyplan.dev/google-benchmark,二手综述,引官方语义)。

`benchmark::ClobberMemory()`:强制编译器把所有挂起的写刷到全局内存,仅 GNU/MSVC 可用。官方例子——`v.push_back(42)` 后调 `ClobberMemory()` 才保证 42 真的写入内存:

```cpp
std::vector<int> v;
v.reserve(1);
auto data = v.data();
benchmark::DoNotOptimize(data);
v.push_back(42);
benchmark::ClobberMemory();  // 强制 42 落内存
```

### 底层实现与 `volatile` 作为粗糙手段的局限

`DoNotOptimize` 底层是 inline asm + `volatile`,典型实现 `asm volatile("" : "+r,m"(value) : : "memory");`:

- `volatile` 让编译器不得删除/优化这个空 asm 块——这是它在 `-O2` 下能挡住 DCE 的根。
- `"memory"` clobber 阻止跨屏障的重排,并强制内存副作用被观察到。
- **编译器相关坑**:GCC 用 `"+m,r"` 约束会生成多余的 `memcpy`(clang/icc 不受影响),改成 `"+r,m"` 可避免——约束串顺序会实质改变行为与开销。
- **裸 `volatile` 变量的局限**:直接给变量加 `volatile` 是更粗糙的手段——它强制每次访问都读写内存(引入并不属于被测代码的内存流量开销),且不像 `DoNotOptimize` 那样精确地只在测量点设屏障,容易测出失真的偏高结果,也无法表达"保护输入不被常量折叠"的语义。
- **未来失效风险**:防优化依赖当前编译器的分析能力,新版本可能引入新分析把你今天没被删的循环删掉——基准代码需随编译器演进复核。
- 来源:theunixzoo.co.uk 博客 + google/benchmark issue #1340(二手,但含可验证的 asm 细节)。

---

## 各语言防优化 API 速查表

| 语言 | 防 DCE/防消费缺失 | 防输入常量折叠 | 自动迭代/计时 | 统计/预热 | 一手出处 |
| --- | --- | --- | --- | --- | --- |
| **Go (1.24+)** | `for b.Loop(){}`(自动 `runtime.KeepAlive` 包裹循环体变量) | `b.Loop()` 同时保持入参存活;输入来自非常量则自然不折叠 | `b.Loop()` 自动 reset/stop 计时,单次调用 | `b.N` 自适应放大迭代;ns/op 均值 | pkg.go.dev/testing;go.dev/blog/testing-b-loop |
| **Go (传统)** | 结果写包级变量 `var result T`(sink) | 输入用运行期值,避免常量入参 | `b.ResetTimer()`/`StopTimer()` 手动 | `b.N` 自适应;`b.ReportAllocs()` | dave.cheney.net 2013 |
| **Rust** | `std::hint::black_box(x)`(保护返回值) | `black_box(input)`(强制求值,即使返回值未用) | criterion 自动管样本与迭代 | criterion:warm-up + bootstrap + Tukey 离群分类 | doc.rust-lang.org/std/hint;criterion.rs |
| **C++ (Google Benchmark)** | `benchmark::DoNotOptimize(result)`(先物化到局部再传) | `DoNotOptimize(input)`(对输入也调,逼成未知值) | `for (auto _ : state)` 自动迭代 | 大迭代数摊薄;`state.PauseTiming/ResumeTiming` | google.github.io/benchmark |
| **C++ (内存可见)** | `benchmark::ClobberMemory()`(刷挂起写,仅 GNU/MSVC) | 同上 | — | — | google.github.io/benchmark |
| **C++ (粗糙手段)** | `volatile` 变量(每次强制读写内存) | 无法表达 | — | — | (限局:引入额外内存开销、不精确;见正文) |

---

## 来源清单

可信度标注:一手 = 官方文档 / 标准库 / 语言作者本人;二手 = 第三方综述(语义可追溯官方)。

1. **[一手]** Go 标准库 `testing` 包文档 — `b.Loop()`/`b.N`/`ResetTimer`/`ReportAllocs` 原文。https://pkg.go.dev/testing
2. **[一手]** Go 官方博客 "More predictable benchmarking with testing.B.Loop"(Go 1.24)— `b.Loop()` 防 DCE(禁内联)、自动计时、单次调用的设计动机。https://go.dev/blog/testing-b-loop
3. **[一手,作者博客]** Dave Cheney(Go 核心贡献者)"How to write benchmarks in Go" — 包级变量 sink 模式防 DCE 的经典指引与代码。https://dave.cheney.net/2013/06/30/how-to-write-benchmarks-in-go
4. **[一手]** Rust 标准库 `std::hint::black_box` 文档 — 语义、双重作用、best-effort 局限、const eval no-op。https://doc.rust-lang.org/std/hint/fn.black_box.html
5. **[一手]** criterion.rs User Guide — `bench_with_input` 自动 `black_box`。https://bheisler.github.io/criterion.rs/book/user_guide/benchmarking_with_inputs.html
6. **[一手]** criterion.rs Analysis — warm-up / sampling / Tukey 离群分类 / bootstrap 重采样 / T 检验回归对比的统计方法。https://bheisler.github.io/criterion.rs/book/analysis.html
7. **[一手]** Google Benchmark User Guide — `DoNotOptimize()`(只保护结果不保护表达式的反例)、`ClobberMemory()`、推荐物化模式。https://google.github.io/benchmark/user_guide.html
8. **[二手]** studyplan.dev "C++ Micro-benchmarking: DoNotOptimize, ClobberMemory and DCE" — 输入常量折叠陷阱(`10+20→30`)的展开讲解,语义可追溯 Google Benchmark 官方。https://www.studyplan.dev/google-benchmark/micro-benchmarks
9. **[二手]** theunixzoo.co.uk "Preventing an optimising compiler from removing or reordering your code" — `asm volatile("" : ... : "memory")` 底层机制,`volatile` 阻止删除空 asm 块。https://theunixzoo.co.uk/blog/2021-10-14-preventing-optimisations.html
10. **[二手]** google/benchmark Issue #1340 — GCC 下 `DoNotOptimize` 约束串 `"+m,r"` vs `"+r,m"` 引入多余 memcpy 的编译器相关坑。https://github.com/google/benchmark/issues/1340

> 一手来源:7 / 10 条(条目 1-7),占比 70%,满足 >50% 要求。三个硬指标出处齐备:Go `testing.B.Loop`(条目 1+2)、Rust `black_box`(条目 4)、C++ `DoNotOptimize`(条目 7)。
