---
name: java-performance
description: Java 性能优化规范 — JFR 生产 profiling、JMH 基准测试、Generational ZGC / G1GC 调优、GraalVM Native Image、CDS、async-profiler 火焰图、Micrometer 指标。当用户排查性能瓶颈、内存泄漏、GC 停顿、优化吞吐/延迟，或讨论 "性能优化"、"JFR"、"JMH"、"GC 调优"、"ZGC"、"Native Image"、"火焰图"、"profiling"、"benchmark" 时加载。
model: sonnet
---

# Java 性能优化规范

## 核心方法论

**数据驱动，禁猜测**：profile → 找热点 → 改 → JMH 验证 → 回归测试。

## 硬约束

1. **生产环境持续开 JFR** (`disk=true,maxsize=500m,maxage=1d`)
2. **优化前必有基线数据** (JFR + JMH 或 Micrometer)
3. **优化后必有 JMH 统计验证** (置信区间不重叠才算显著)
4. **每次只改一个变量**
5. **Java 25 默认评估 Generational ZGC** (低延迟场景)
6. **parallelStream 仅 CPU 密集 + 数据量 >10K** 时使用
7. **集合预设初始容量**，避免 resize
8. **避免装箱**：`IntStream` / `LongStream` 处理原始类型

## JFR (Java Flight Recorder)

```bash
# 启动时持续记录 (生产推荐)
java -XX:StartFlightRecording=disk=true,maxsize=500m,maxage=1d \
     -XX:FlightRecorderOptions=stackdepth=256 \
     -jar app.jar

# 运行时按需
jcmd <pid> JFR.start duration=60s filename=run.jfr settings=profile
jcmd <pid> JFR.dump  filename=now.jfr

# 离线分析
jfr summary run.jfr
jfr print --events jdk.CPULoad,jdk.GarbageCollection run.jfr
# 或 JMC GUI (https://www.oracle.com/java/technologies/jdk-mission-control.html)
```

**关注事件**：
- CPU 热点：`jdk.ExecutionSample`、`jdk.CPULoad`
- 内存分配：`jdk.ObjectAllocationInNewTLAB`、`jdk.OldObjectSample`
- GC 停顿：`jdk.GarbageCollection`、`jdk.GCPhasePause`
- 锁竞争：`jdk.JavaMonitorEnter`、`jdk.ThreadPark`
- 虚拟线程 pin：`jdk.VirtualThreadPinned`

## JMH 基准测试

```java
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Benchmark)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
public class CollectionBenchmark {
    private List<String> data;

    @Setup public void setup() {
        data = IntStream.range(0, 10_000).mapToObj(i -> "item-" + i).toList();
    }

    @Benchmark public long streamCount() {
        return data.stream().filter(s -> s.contains("5")).count();
    }

    @Benchmark public long parallelStream() {
        return data.parallelStream().filter(s -> s.contains("5")).count();
    }
}
```

```groovy
// build.gradle
plugins { id 'me.champeau.jmh' version '0.7.2' }
jmh { warmupIterations = 3; iterations = 5; fork = 2; resultFormat = 'JSON' }
```

```bash
./gradlew jmh
```

## GC 调优 (Java 25)

### Generational ZGC (低延迟首选)

```bash
java -XX:+UseZGC -XX:+ZGenerational \
     -Xms4g -Xmx4g \
     -jar app.jar
```

- 停顿 < 1ms
- 堆 8MB ~ 16TB
- 适合：金融、实时 API、长 GC 敏感

### G1GC (通用)

```bash
java -XX:+UseG1GC -XX:MaxGCPauseMillis=200 \
     -XX:G1HeapRegionSize=16m -XX:+G1UseAdaptiveIHOP \
     -Xms4g -Xmx4g -jar app.jar
```

### GC 日志统一格式

```bash
java -Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=100m -jar app.jar
# 分析：GCEasy.io、GCViewer
```

## 启动优化

```bash
# CDS (Class Data Sharing) — 轻量，启动提速 20-40%
java -XX:ArchiveClassesAtExit=app.jsa -jar app.jar    # 1) 创建归档
java -XX:SharedArchiveFile=app.jsa    -jar app.jar    # 2) 复用

# GraalVM Native Image — 启动 <100ms，内存 -50~80%
./gradlew nativeCompile
./build/native/nativeCompile/my-app

# 适用：Serverless、CLI、低内存容器；不适：反射重度依赖
```

## 常见优化模式

```java
// 集合预容量
List<User> users = new ArrayList<>(expectedSize);
Map<String, User> map = HashMap.newHashMap(expectedSize);  // Java 19+

// 字符串
String result = String.join(",", list);           // 替代手动循环
String s = "name=%s, age=%d".formatted(n, a);     // 替代 String.format

// 原始 Stream，避免装箱
IntStream.range(0, 100).sum();
OptionalInt max = IntStream.of(1, 2, 3).max();

// 不可变 List
List<T> result = stream.toList();   // Java 16+

// JPA fetch 防 N+1
@Query("SELECT u FROM User u JOIN FETCH u.orders WHERE u.id IN :ids")
List<User> findAllWithOrders(@Param("ids") List<Long> ids);

// HikariCP
// spring.datasource.hikari.maximum-pool-size=10
// spring.datasource.hikari.minimum-idle=5
// spring.datasource.hikari.connection-timeout=2000
```

## Micrometer 指标

```java
@Timed(value = "user.query", percentiles = {0.5, 0.95, 0.99})
public Optional<User> findById(Long id) { ... }

@Bean
public TimedAspect timedAspect(MeterRegistry r) { return new TimedAspect(r); }
```

**四大黄金指标**：延迟 (P50/P95/P99/P999)、吞吐 (QPS/TPS)、错误率、饱和度。

## async-profiler 火焰图

```bash
./asprof -d 30 -f cpu.html   <pid>   # CPU
./asprof -d 30 -e alloc -f alloc.html <pid>  # 分配
./asprof -d 30 -e lock  -f lock.html  <pid>  # 锁竞争
./asprof -d 30 -e wall  -f wall.html  <pid>  # 含等待时间
```

## Red Flags

| AI 易犯解释 | 实际应核验 |
|---------|---------|
| "凭经验改" | 是否有 JFR/JMH 数据？ |
| "看起来慢" | 是否是 profiling 热点？ |
| "快了 10%" | 是否 JMH 置信区间验证？ |
| "G1 够用" | 是否评估 Generational ZGC？ |
| "JVM 默认参数" | 是否按负载调优？ |
| "parallelStream 更快" | 数据是否 >10K + CPU 密集？ |
| "Native Image 太麻烦" | Serverless/CLI 是否评估？ |

## 检查清单

- [ ] 生产开 JFR (disk + maxage)
- [ ] JMH 基线 + 优化后对比
- [ ] GC 选型有数据依据 (ZGC vs G1)
- [ ] 启动优化评估 (CDS / Native)
- [ ] 集合预容量
- [ ] 无不必要装箱
- [ ] HikariCP 参数与负载匹配
- [ ] JPA `JOIN FETCH` 防 N+1
- [ ] Micrometer 四大指标接入
- [ ] async-profiler 火焰图存档

## 参考

- JFR 文档: https://docs.oracle.com/en/java/javase/25/troubleshoot/diagnostic-tools.html
- JMH 官方: https://openjdk.org/projects/code-tools/jmh/
- ZGC: https://wiki.openjdk.org/display/zgc
- GraalVM Native: https://www.graalvm.org/latest/reference-manual/native-image/
- async-profiler: https://github.com/async-profiler/async-profiler
