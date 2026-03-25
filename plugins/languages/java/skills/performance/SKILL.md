---
name: performance
description: Java 性能优化规范 - JFR、JMH 基准测试、ZGC/G1GC 调优、GraalVM Native Image、async-profiler。优化性能时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Java 性能优化规范

## 适用 Agents

- **java:dev** - 性能感知的代码编写
- **java:perf** - 专业性能分析和优化
- **java:debug** - 性能瓶颈排查

## 相关 Skills

- **Skills(java:core)** - Java 21+ 特性、Stream API 性能
- **Skills(java:concurrency)** - Virtual Threads、并发性能
- **Skills(java:spring)** - Micrometer 监控、Actuator

## JFR（Java Flight Recorder）

JFR 是 JDK 内置的生产级 profiling 工具，开销 < 1%。

```bash
# 启动时开启 JFR
java -XX:StartFlightRecording=duration=120s,filename=app.jfr \
     -XX:FlightRecorderOptions=stackdepth=256 \
     -jar app.jar

# 运行时开启 JFR
jcmd <pid> JFR.start duration=60s filename=recording.jfr

# 持续记录（生产推荐）
java -XX:StartFlightRecording=disk=true,maxsize=500m,maxage=1d \
     -jar app.jar

# 分析 JFR 文件
jfr print --events jdk.CPULoad,jdk.GarbageCollection recording.jfr
jfr summary recording.jfr
```

### JFR 关注事件
- **CPU**：jdk.CPULoad、jdk.ExecutionSample（热点方法）
- **内存**：jdk.ObjectAllocationInNewTLAB、jdk.OldObjectSample（泄漏）
- **GC**：jdk.GarbageCollection、jdk.GCPhasePause（停顿）
- **线程**：jdk.JavaMonitorEnter（锁竞争）、jdk.ThreadPark（等待）
- **I/O**：jdk.FileRead、jdk.SocketRead（I/O 延迟）

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

    @Setup
    public void setup() {
        data = IntStream.range(0, 10_000)
            .mapToObj(i -> "item-" + i)
            .toList();
    }

    @Benchmark
    public long streamCount(Blackhole bh) {
        return data.stream()
            .filter(s -> s.contains("5"))
            .count();
    }

    @Benchmark
    public long parallelStreamCount(Blackhole bh) {
        return data.parallelStream()
            .filter(s -> s.contains("5"))
            .count();
    }

    @Benchmark
    public long forLoopCount(Blackhole bh) {
        long count = 0;
        for (String s : data) {
            if (s.contains("5")) count++;
        }
        return count;
    }
}
```

```groovy
// build.gradle JMH 配置
plugins {
    id 'me.champeau.jmh' version '0.7.2'
}

jmh {
    warmupIterations = 3
    iterations = 5
    fork = 2
    resultFormat = 'JSON'
}
```

## GC 调优（Java 21+）

### ZGC（低延迟推荐）
```bash
# ZGC Generational（Java 21+ 默认分代模式）
java -XX:+UseZGC \
     -XX:+ZGenerational \
     -Xmx4g -Xms4g \
     -jar app.jar

# ZGC 特性：
# - 最大停顿 < 1ms（亚毫秒级）
# - 堆大小 8MB ~ 16TB
# - 适合延迟敏感型应用
```

### G1GC（通用推荐）
```bash
# G1GC（吞吐和延迟平衡）
java -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:G1HeapRegionSize=16m \
     -XX:+G1UseAdaptiveIHOP \
     -Xmx4g -Xms4g \
     -jar app.jar
```

### GC 日志分析
```bash
# 启用 GC 日志（统一日志框架 Java 9+）
java -Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=100m \
     -jar app.jar

# 分析工具：GCViewer、GCEasy.io
```

## GraalVM Native Image

```bash
# 编译 Native Image（Spring Boot 3+）
./gradlew nativeCompile

# 特性：
# - 启动时间 < 100ms（vs JVM ~2s）
# - 内存占用降低 50-80%
# - 适合 Serverless、CLI 工具

# CDS（Class Data Sharing）- 轻量替代方案
# 步骤 1: 创建共享归档
java -XX:ArchiveClassesAtExit=app.jsa -jar app.jar
# 步骤 2: 使用共享归档启动（启动提速 20-40%）
java -XX:SharedArchiveFile=app.jsa -jar app.jar
```

## 常见优化模式

```java
// 1. 集合初始化容量（避免 resize）
List<User> users = new ArrayList<>(expectedSize);
Map<String, User> map = HashMap.newHashMap(expectedSize);  // Java 19+

// 2. 字符串优化
String result = String.join(",", list);  // 替代循环拼接
String formatted = "name=%s, age=%d".formatted(name, age);  // 替代 String.format

// 3. 避免装箱/拆箱
IntStream.range(0, 100).sum();  // 使用原始类型 Stream
OptionalInt max = IntStream.of(1, 2, 3).max();  // OptionalInt

// 4. Stream 性能
list.stream().toList();         // 返回不可变 List（Java 16+）
list.parallelStream()           // 仅用于 CPU 密集 + 大数据集 (>10K)

// 5. 连接池配置（HikariCP）
// spring.datasource.hikari.maximum-pool-size=10
// spring.datasource.hikari.minimum-idle=5
// spring.datasource.hikari.idle-timeout=30000

// 6. JPA 批量操作（避免 N+1）
@Query("SELECT u FROM User u JOIN FETCH u.orders WHERE u.id IN :ids")
List<User> findAllWithOrdersByIds(@Param("ids") List<Long> ids);
```

## 性能监控指标

```java
// Micrometer 自定义指标
@Bean
public TimedAspect timedAspect(MeterRegistry registry) {
    return new TimedAspect(registry);
}

@Timed(value = "user.query", percentiles = {0.5, 0.95, 0.99})
public Optional<User> findById(Long id) { ... }

// 关键指标（四大黄金指标）
// 1. 延迟：P50 / P95 / P99 / P999
// 2. 吞吐量：QPS / TPS
// 3. 错误率：4xx / 5xx 比例
// 4. 饱和度：CPU%、内存%、线程池使用率
```

## async-profiler 火焰图

```bash
# CPU 火焰图
./asprof -d 30 -f cpu.html <pid>

# 内存分配火焰图
./asprof -d 30 -e alloc -f alloc.html <pid>

# 锁竞争火焰图
./asprof -d 30 -e lock -f lock.html <pid>

# Wall clock（包含等待时间）
./asprof -d 30 -e wall -f wall.html <pid>
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "凭经验优化就行" | 是否使用 JFR/async-profiler 数据驱动？ |
| "这段代码看起来慢" | 是否确认是 profiling 热点？ |
| "优化完了更快了" | 是否 JMH 统计验证了显著性？ |
| "G1GC 够用了" | Java 21+ 是否评估了 ZGC Generational？ |
| "JVM 默认参数就好" | 是否根据负载特征调优 GC 和堆大小？ |
| "parallelStream 更快" | 数据量是否足够大（>10K）且是 CPU 密集？ |
| "Native Image 不需要" | Serverless 场景是否评估了启动时间？ |

## 检查清单

- [ ] JFR 基线记录（生产环境持续记录）
- [ ] JMH 基准测试关键路径
- [ ] ZGC/G1GC 根据场景选择并调优
- [ ] 集合预设初始容量
- [ ] 避免不必要的装箱/拆箱
- [ ] HikariCP 连接池参数配置
- [ ] JPA batch_size 配置（避免 N+1）
- [ ] Micrometer 关键指标监控
- [ ] async-profiler 火焰图分析
- [ ] GraalVM Native Image / CDS 评估启动优化
