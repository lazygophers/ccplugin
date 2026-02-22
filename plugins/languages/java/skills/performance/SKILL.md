---
name: performance
description: Java 性能优化规范：JVM 调优、GC 优化、性能分析。优化性能时必须加载。
---

# Java 性能优化规范

## 相关 Skills

| 场景     | Skill               | 说明                    |
| -------- | ------------------- | ----------------------- |
| 核心规范 | Skills(core)        | Java 21+ 特性、强制约定 |
| 并发编程 | Skills(concurrency) | Virtual Threads         |

## JVM 参数

```bash
# 内存设置
-Xms2g -Xmx2g

# GC 选择（Java 21+ 推荐 ZGC）
-XX:+UseZGC

# ZGC 调优
-XX:ZCollectionInterval=5
-XX:ZAllocationSpikeTolerance=5

# G1GC（备选）
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
```

## 性能分析

```bash
# JFR (Java Flight Recorder)
java -XX:StartFlightRecording=duration=60s,filename=recording.jfr -jar app.jar

# jcmd
jcmd <pid> JFR.start duration=60s filename=recording.jfr

# jstat
jstat -gc <pid> 1000
```

## 常见优化

```java
// 字符串拼接
String result = String.join(",", list);
StringBuilder sb = new StringBuilder();

// 集合初始化
List<User> users = new ArrayList<>(expectedSize);
Map<String, User> map = new HashMap<>(expectedSize);

// Stream 并行
list.parallelStream().map(this::process).toList();

// 避免装箱
IntStream.range(0, 100).sum();
```

## 检查清单

- [ ] 使用 ZGC（Java 21+）
- [ ] 设置合适的堆内存
- [ ] 使用 JFR 分析性能
- [ ] 避免不必要的对象创建
