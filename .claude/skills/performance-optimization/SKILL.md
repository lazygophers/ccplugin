---
description: 性能优化 - 性能瓶颈定位、优化策略、基准测试、性能监控
user-invocable: false
context: fork
model: sonnet
---

# 性能优化（Performance Optimization）

本 Skill 提供系统化的性能优化指导，从瓶颈定位到优化实施，确保系统高效运行。

## 概览

**核心能力**：
1. **性能瓶颈定位** - 使用profiling工具识别热点
2. **优化策略** - 算法优化、缓存策略、异步处理
3. **基准测试** - 性能基线、对比测试
4. **性能监控** - 实时监控、告警机制
5. **资源优化** - CPU、内存、I/O优化

**性能指标**：
- **响应时间**：API延迟、页面加载时间
- **吞吐量**：QPS、TPS
- **资源使用**：CPU使用率、内存占用、磁盘I/O

## 执行流程

### 阶段1：性能瓶颈定位

**目标**：识别性能问题的根本原因

**步骤**：
1. **使用Profiling工具**：
   - **Python**：cProfile、py-spy、line_profiler
   - **JavaScript**：Chrome DevTools、Node.js --prof
   - **Go**：pprof
   - **Java**：JProfiler、VisualVM

2. **常见瓶颈**：
   - **N+1查询问题**：数据库查询过多
   - **低效算法**：O(n²)算法应优化为O(n log n)
   - **内存泄漏**：未释放的对象
   - **同步阻塞**：等待I/O操作
   - **缓存缺失**：频繁访问数据库

3. **性能分析报告**：
   ```
   热点函数（Top 5）：
   1. database_query() - 45% CPU时间
   2. json_serialize() - 20% CPU时间
   3. image_resize() - 15% CPU时间
   4. validate_input() - 10% CPU时间
   5. log_request() - 5% CPU时间
   ```

### 阶段2：优化策略

**目标**：选择合适的优化策略

**步骤**：
1. **算法优化**：
   ```python
   # 优化前：O(n²)
   def find_duplicates_slow(items):
       duplicates = []
       for i in range(len(items)):
           for j in range(i + 1, len(items)):
               if items[i] == items[j]:
                   duplicates.append(items[i])
       return duplicates

   # 优化后：O(n)
   def find_duplicates_fast(items):
       seen = set()
       duplicates = set()
       for item in items:
           if item in seen:
               duplicates.add(item)
           seen.add(item)
       return list(duplicates)
   ```

2. **缓存策略**：
   ```python
   from functools import lru_cache

   # 函数级缓存
   @lru_cache(maxsize=128)
   def expensive_computation(n):
       # 复杂计算
       return result

   # 数据库查询缓存（Redis）
   def get_user(user_id):
       cache_key = f"user:{user_id}"
       cached = redis.get(cache_key)
       if cached:
           return json.loads(cached)

       user = db.query(User).get(user_id)
       redis.setex(cache_key, 3600, json.dumps(user))
       return user
   ```

3. **异步处理**：
   ```python
   # 同步（阻塞）
   def process_orders():
       for order in orders:
           send_email(order)  # 阻塞
           update_inventory(order)

   # 异步（非阻塞）
   async def process_orders():
       tasks = [
           send_email_async(order)
           for order in orders
       ]
       await asyncio.gather(*tasks)
       update_inventory_batch(orders)
   ```

4. **数据库优化**：
   - **索引优化**：为查询字段添加索引
   - **查询优化**：避免SELECT *，只查询需要的字段
   - **批量操作**：批量插入/更新而非逐条操作
   - **连接池**：复用数据库连接
   - **读写分离**：主库写，从库读

### 阶段3：基准测试

**目标**：建立性能基线，验证优化效果

**步骤**：
1. **编写基准测试**：
   ```python
   import time

   def benchmark(func, *args, iterations=1000):
       start = time.time()
       for _ in range(iterations):
           func(*args)
       duration = time.time() - start
       avg_time = (duration / iterations) * 1000  # ms
       return avg_time

   # 测试
   slow_time = benchmark(find_duplicates_slow, large_list)
   fast_time = benchmark(find_duplicates_fast, large_list)

   print(f"优化前：{slow_time:.2f}ms")
   print(f"优化后：{fast_time:.2f}ms")
   print(f"提升：{(slow_time / fast_time):.2f}x")
   ```

2. **负载测试**：
   ```bash
   # 使用 Apache Bench
   ab -n 10000 -c 100 http://localhost:8000/api/users

   # 使用 k6
   k6 run --vus 100 --duration 30s load-test.js
   ```

3. **性能基线**：
   ```
   基准性能（优化前）：
   - 响应时间（P95）：500ms
   - QPS：200
   - CPU使用率：80%
   - 内存使用：2GB

   优化目标：
   - 响应时间（P95）：<200ms（提升60%）
   - QPS：>500（提升150%）
   - CPU使用率：<50%
   - 内存使用：<1.5GB
   ```

### 阶段4：性能监控

**目标**：持续监控性能，及时发现问题

**步骤**：
1. **监控指标**：
   - **Golden Signals**（4个黄金指标）：
     - **Latency**（延迟）：请求响应时间
     - **Traffic**（流量）：请求量
     - **Errors**（错误）：错误率
     - **Saturation**（饱和度）：资源使用率

2. **监控工具**：
   - **APM**：New Relic、Datadog、Sentry
   - **日志**：ELK Stack（Elasticsearch + Logstash + Kibana）
   - **指标**：Prometheus + Grafana
   - **追踪**：Jaeger、Zipkin

3. **告警配置**：
   ```yaml
   # Prometheus alerting rules
   groups:
     - name: performance
       rules:
         - alert: HighResponseTime
           expr: http_request_duration_seconds{quantile="0.95"} > 0.5
           for: 5m
           annotations:
             summary: "响应时间过高"
             description: "P95响应时间 > 500ms"

         - alert: HighErrorRate
           expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
           annotations:
             summary: "错误率过高"
             description: "5xx错误率 > 5%"
   ```

### 阶段5：资源优化

**目标**：优化CPU、内存、I/O使用

**步骤**：
1. **CPU优化**：
   - 避免CPU密集计算（考虑异步或分布式）
   - 使用多线程/多进程
   - 优化算法复杂度

2. **内存优化**：
   ```python
   # 使用生成器而非列表（节省内存）
   def read_large_file_bad(filename):
       return open(filename).readlines()  # 全部加载到内存

   def read_large_file_good(filename):
       with open(filename) as f:
           for line in f:  # 逐行读取
               yield line

   # 及时释放大对象
   large_data = load_large_dataset()
   process(large_data)
   del large_data  # 显式释放
   ```

3. **I/O优化**：
   - 使用异步I/O（async/await）
   - 批量读写（减少系统调用）
   - 使用SSD而非HDD
   - 启用压缩（减少网络传输）

## 优化模式

### 1. 缓存模式

**多级缓存**：
```
浏览器缓存 → CDN缓存 → 应用缓存（Redis） → 数据库
```

**缓存策略**：
- **Cache-Aside**：应用管理缓存
- **Write-Through**：写入时同步更新缓存
- **Write-Behind**：异步更新缓存

**缓存失效**：
- **TTL**（Time To Live）：过期时间
- **LRU**（Least Recently Used）：最少使用淘汰
- **手动失效**：业务变更时主动清除

### 2. 异步模式

**消息队列**：
```python
# 同步处理（慢）
def create_order(order_data):
    order = save_order(order_data)
    send_email(order)  # 阻塞
    update_inventory(order)  # 阻塞
    notify_warehouse(order)  # 阻塞
    return order

# 异步处理（快）
def create_order(order_data):
    order = save_order(order_data)
    queue.publish('order.created', order)  # 非阻塞
    return order

# 后台worker处理
def worker():
    while True:
        order = queue.consume('order.created')
        send_email(order)
        update_inventory(order)
        notify_warehouse(order)
```

### 3. 分页模式

```python
# 不好：一次加载所有数据
def get_all_users():
    return db.query(User).all()  # 可能百万条

# 好：分页加载
def get_users_page(page=1, page_size=50):
    offset = (page - 1) * page_size
    return db.query(User).limit(page_size).offset(offset).all()

# 更好：游标分页（适合大数据）
def get_users_cursor(cursor=None, limit=50):
    query = db.query(User).order_by(User.id)
    if cursor:
        query = query.filter(User.id > cursor)
    users = query.limit(limit).all()
    next_cursor = users[-1].id if users else None
    return users, next_cursor
```

## 性能优化清单

### 代码层面
- [ ] 避免N+1查询（使用JOIN或预加载）
- [ ] 优化算法复杂度（O(n²) → O(n log n)）
- [ ] 使用缓存（函数缓存、查询缓存）
- [ ] 异步处理I/O操作
- [ ] 批量操作数据库

### 数据库层面
- [ ] 添加索引（查询字段、JOIN字段）
- [ ] 查询优化（避免SELECT *）
- [ ] 连接池配置
- [ ] 读写分离
- [ ] 数据库分片

### 架构层面
- [ ] 引入缓存层（Redis）
- [ ] 使用CDN（静态资源）
- [ ] 负载均衡
- [ ] 水平扩展
- [ ] 消息队列（异步处理）

### 前端层面
- [ ] 代码压缩（minify）
- [ ] 图片优化（压缩、懒加载）
- [ ] 使用CDN
- [ ] 浏览器缓存
- [ ] 服务端渲染（SSR）

## 工具集成

### Profiling工具
- **Python**：cProfile、py-spy、memory_profiler
- **JavaScript**：Chrome DevTools、Node.js --prof
- **Go**：pprof
- **Java**：JProfiler、VisualVM

### 负载测试工具
- **Apache Bench**：简单快速
- **k6**：现代化、可编程
- **JMeter**：功能强大
- **Locust**：Python编写、分布式

### 监控工具
- **APM**：New Relic、Datadog
- **指标**：Prometheus + Grafana
- **日志**：ELK Stack
- **追踪**：Jaeger、Zipkin

## 输出格式

### 性能优化报告

```markdown
## 性能优化报告

### 优化前基线
- 响应时间（P95）：500ms
- QPS：200
- CPU使用率：80%
- 内存使用：2GB

### 主要瓶颈
1. **N+1查询**：user_orders接口查询数据库1000次
2. **低效算法**：find_duplicates使用O(n²)算法
3. **缺少缓存**：频繁查询用户信息

### 优化措施
1. 使用JOIN预加载订单数据（消除N+1）
2. 优化算法为O(n)（使用哈希表）
3. 添加Redis缓存（TTL 1小时）

### 优化后效果
- 响应时间（P95）：150ms（提升70%）✓
- QPS：600（提升200%）✓
- CPU使用率：40%（降低50%）✓
- 内存使用：1.2GB（降低40%）✓

### 验证测试
- 基准测试：1000次请求，平均响应时间150ms
- 负载测试：100并发，QPS稳定在600
- 压力测试：200并发，无错误
```

## 相关 Skills

- **code-review** - 代码审查（性能问题检测）
- **architecture-review** - 架构评审（性能架构设计）
- **testing** - 测试策略（性能测试）
