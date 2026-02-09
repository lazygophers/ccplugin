# JVM 性能优化规范

## 核心原则

### ✅ 必须遵守

1. **选择合适的 GC** - 根据应用特点选择
2. **设置合理的堆大小** - 避免过小或过大
3. **监控 GC 日志** - 定期分析 GC 行为
4. **优化对象分配** - 减少不必要的对象创建
5. **使用性能分析工具** - JFR、JProfiler 等

## JVM 参数配置

### G1GC（通用推荐）

```bash
# ✅ G1GC 配置（通用）
java -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:G1HeapRegionSize=16m \
     -Xmx4g \
     -Xms4g \
     -XX:+UseStringDeduplication \
     -XX:+PrintGCDetails \
     -XX:+PrintGCTimeStamps \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -jar app.jar

# ✅ G1GC 配置（大堆）
java -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:G1HeapRegionSize=32m \
     -Xmx8g \
     -Xms8g \
     -XX:+UseStringDeduplication \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -jar app.jar
```

### ZGC（低延迟，Java 21+）

```bash
# ✅ ZGC 配置（低延迟）
java -XX:+UseZGC \
     -Xmx4g \
     -Xms4g \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -jar app.jar

# ✅ ZGC 配置（大堆）
java -XX:+UseZGC \
     -Xmx16g \
     -Xms16g \
     -XX:ZCollectionInterval=5 \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -jar app.jar
```

### ParallelGC（吞吐量优先）

```bash
# ✅ ParallelGC 配置（吞吐量优先）
java -XX:+UseParallelGC \
     -XX:MaxGCPauseMillis=200 \
     -Xmx4g \
     -Xms4g \
     -XX:ParallelGCThreads=8 \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -jar app.jar
```

## GC 日志分析

### GC 日志配置

```bash
# ✅ Java 21+ GC 日志格式
-Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m

# ✅ 详细 GC 日志
-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=10m

# ✅ GC + 引用处理
-Xlog:gc+ref*:file=gc.log:time,tags:filecount=5,filesize=10m

# ✅ GC + 类加载
-Xlog:gc+class*:file=gc.log:time,tags:filecount=5,filesize=10m
```

### GC 日志分析工具

```bash
# ✅ GCViewer
java -jar gcviewer.jar gc.log

# ✅ Censum
java -jar censum.jar gc.log

# ✅ GCHisto
java -jar gchisto.jar gc.log
```

## 性能分析工具

### JFR（Java Flight Recorder）

```bash
# ✅ 启动 JFR 记录
java -XX:StartFlightRecording=duration=60s,filename=app.jfr \
     -jar app.jar

# ✅ 持续记录
java -XX:StartFlightRecording=dumponexit=true,filename=app.jfr,maxage=24h \
     -jar app.jar

# ✅ 程序控制 JFR
import jdk.jfr.Recording;
import jdk.jfr.configuration.RecordingOptions;

Recording recording = new Recording();
recording.start();

// ... 执行程序 ...

recording.dump("recording.jfr");
recording.close();
```

### JMC（Java Mission Control）

```bash
# ✅ 打开 JFR 文件
jmc recording.jfr

# ✅ 分析内容
- CPU 使用
- 内存分配
- GC 事件
- 线程活动
- 锁竞争
- 方法调用
```

### VisualVM

```bash
# ✅ 启动 VisualVM
visualvm

# ✅ 连接到运行中的应用
- 监控 CPU
- 监控内存
- 线程转储
- 堆转储
```

## 内存优化

### 减少对象分配

```java
// ✅ 复用对象
private static final DateTimeFormatter DATE_FORMATTER =
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

public String format(LocalDateTime dateTime) {
    return dateTime.format(DATE_FORMATTER);
}

// ✅ 使用基本类型
private int[] values;  // ✅
private Integer[] values;  // ❌ 除非需要 null

// ✅ 使用对象池
private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

// ✅ 使用 StringBuilder
StringBuilder sb = new StringBuilder();
for (String item : items) {
    sb.append(item);
}
String result = sb.toString();

// ❌ 避免字符串拼接循环
String result = "";
for (String item : items) {
    result += item;  // 每次循环创建新对象
}
```

### 集合优化

```java
// ✅ 预设初始容量
List<User> users = new ArrayList<>(1000);
Map<Long, User> userMap = new HashMap<>(1000);

// ✅ 使用原始类型集合（Eclipse Collections）
IntArrayList intList = new IntArrayList();
LongLongHashMap map = new LongLongHashMap();

// ✅ 使用不可变集合
List<String> immutable = List.of("a", "b", "c");
```

## 线程优化

### 线程池配置

```java
// ✅ CPU 密集型
int cores = Runtime.getRuntime().availableProcessors();
ExecutorService cpuExecutor = Executors.newFixedThreadPool(cores);

// ✅ I/O 密集型（传统线程池）
int ioThreads = cores * 2;
ExecutorService ioExecutor = Executors.newFixedThreadPool(ioThreads);

// ✅ Virtual Threads（推荐）
ExecutorService vThreadExecutor = Executors.newVirtualThreadPerTaskExecutor();

// ✅ 自定义线程池配置
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    cores,              // 核心线程数
    cores * 2,          // 最大线程数
    60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(1000),
    new ThreadFactoryBuilder()
        .setNameFormat("worker-%d")
        .setDaemon(true)
        .build(),
    new ThreadPoolExecutor.CallerRunsPolicy()  // 拒绝策略
);
```

## 性能最佳实践

### 避免常见性能问题

```java
// ✅ 避免 N+1 查询
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
Optional<User> findByIdWithOrders(@Param("id") Long id);

// ❌ N+1 查询
User user = userRepository.findById(id);
for (Order order : user.getOrders()) {  // N+1 问题
    // ...
}

// ✅ 批量操作
@Modifying
@Query("UPDATE User u SET u.status = :status WHERE u.id IN :ids")
void updateStatus(@Param("ids") List<Long> ids, @Param("status") UserStatus status);

// ✅ 批量插入
@Transactional
public void batchInsert(List<User> users) {
    jdbcTemplate.batchUpdate(
        "INSERT INTO user (email, name) VALUES (?, ?)",
        users.stream()
            .map(u -> new Object[]{u.email(), u.name()})
            .toList()
    );
}

// ✅ 使用缓存
@Cacheable("users")
public User getUserById(Long id) {
    return userRepository.findById(id).orElse(null);
}
```

### 性能测试

```java
// ✅ JMH 基准测试
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@State(Scope.Benchmark)
public class MyBenchmark {

    private List<String> list;

    @Setup
    public void setup() {
        list = IntStream.range(0, 1000)
            .mapToObj(i -> "item-" + i)
            .toList();
    }

    @Benchmark
    public void testForEach() {
        list.forEach(item -> process(item));
    }

    @Benchmark
    public void testStream() {
        list.stream().forEach(this::process);
    }

    private void process(String item) {
        // 处理逻辑
    }
}

// ✅ 运行 JMH
java -jar target/benchmarks.jar MyBenchmark
```

## 监控指标

### 关键指标

```bash
# ✅ JVM 参数（包含所有监控）
java -XX:+UseG1GC \
     -Xmx4g -Xms4g \
     -XX:+PrintGCDetails -XX:+PrintGCTimeStamps \
     -Xlog:gc*:file=gc.log:time,tags:filecount=5,filesize=10m \
     -XX:+PrintConcurrentLocks \
     -XX:+FlightRecorder \
     -XX:StartFlightRecording=filename=recording.jfr,dumponexit=true,maxage=24h \
     -Dcom.sun.management.jmxremote \
     -Dcom.sun.management.jmxremote.port=9010 \
     -Dcom.sun.management.jmxremote.authenticate=false \
     -Dcom.sun.management.jmxremote.ssl=false \
     -jar app.jar
```

### 监控内容

- **堆内存**：使用量、GC 后大小
- **GC**：频率、停顿时间、GC 类型
- **线程**：数量、状态、死锁
- **CPU**：使用率
- **类加载**：加载、卸载数量

## 检查清单

- [ ] 选择合适的 GC
- [ ] 堆大小合理（Xmx = Xms）
- [ ] GC 日志已配置
- [ ] 使用 JFR 进行性能分析
- [ ] 减少 N+1 查询
- [ ] 使用缓存
- [ ] 线程池配置合理
- [ ] 监控指标完整
