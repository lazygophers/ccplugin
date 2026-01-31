---
name: lrpc-queue-skills
description: lazygophers/lrpc queue 模块完整指南 - 分布式消息队列中间件
---

# LRPC Queue 模块使用指南

## 概述

`lrpc/middleware/storage/queue` 是一个功能完整的分布式消息队列中间件，支持三种存储后端（Memory、Redis Streams、Kafka），提供统一的消息队列 API。

### 核心特性

- **多后端支持**：Memory（内存）、Redis Streams、Kafka
- **泛型设计**：支持任意类型的消息体
- **Topic-Channel 模型**：发布订阅模式，一个 Topic 可有多个 Channel
- **消费者组支持**：Redis Streams 和 Kafka 原生消费者组
- **消息确认机制**：Ack/Nack 机制
- **消息过期**：支持 TTL（Time To Live）
- **重试机制**：可配置的重试次数和延迟
- **并发控制**：MaxInFlight 限制并发消费数
- **批量操作**：批量发布和消费

## 支持的队列类型

### 1. Memory Queue（内存队列）

**特点**：
- 最快性能，无网络开销
- 不持久化，进程重启丢失
- 单机使用，适合测试和开发
- 使用 `sync.Cond` 实现阻塞等待

**使用场景**：单元测试、开发环境、单机应用

```go
q := queue.NewQueue(&queue.Config{
    StorageType: queue.StorageMemory,
})
defer q.Close()
```

### 2. Redis Streams Queue

**特点**：
- 基于 Redis 5.0+ Streams 数据结构
- 持久化存储，支持主从复制
- 原生消费者组支持
- 消息自动清理（MaxLen）
- 使用 XREADGROUP 阻塞读取

**键名格式**：`{prefix}{topic}:{channel}`
- 默认前缀：`lrpc:queue:`
- 示例：`lrpc:queue:events:handlers`

**使用场景**：中小规模生产环境、需要持久化的单机应用

```go
q := queue.NewQueue(&queue.Config{
    StorageType: queue.StorageRedis,
    RedisConfig: &queue.RedisConfig{
        Addr:      "localhost:6379",
        KeyPrefix: "myapp:queue:",
        DB:        0,
    },
})
defer q.Close()

// 或使用外部 Redis 客户端
client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
q := queue.NewQueue(&queue.Config{
    StorageType: queue.StorageRedis,
    RedisClient: client,
})
```

### 3. Kafka Queue

**特点**：
- 分布式、高吞吐量
- 分区支持，水平扩展
- 消息压缩（gzip/snappy/lz4/zstd）
- Offset 提交机制
- 自动创建 Topic（可选）

**Topic 命名**：`{prefix}{topic}`
- 默认前缀：`lrpc-queue-`
- 示例：`lrpc-queue-events`

**消费者组**：每个 Channel 使用独立的消费者组
- 组 ID：`{prefix}{topic}-{channel}`

**使用场景**：大规模生产环境、需要高吞吐和分区

```go
q := queue.NewQueue(&queue.Config{
    StorageType: queue.StorageKafka,
    KafkaConfig: &queue.KafkaConfig{
        Brokers:            []string{"localhost:9092"},
        TopicPrefix:        "myapp-queue-",
        Partition:          3,
        ReplicationFactor:  2,
        AutoCreateTopics:   true,
        CompressionType:    "gzip",
        RequiredAcks:       1,
    },
})
defer q.Close()
```

## 核心 API

### 1. 生产者 API（Topic 接口）

```go
type Topic[T any] interface {
    // 发布消息（自动生成 ID 和时间戳）
    Pub(msg T) error

    // 批量发布消息
    PubBatch(msgs []T) error

    // 发布完整消息（包含元数据）
    PubMsg(msg *Message[T]) error

    // 批量发布完整消息
    PubMsgBatch(msgs []*Message[T]) error

    // Channel 管理
    GetOrAddChannel(name string, config *ChannelConfig) (Channel[T], error)
    GetChannel(name string) (Channel[T], error)
    ChannelList() []string

    // 生命周期
    Close() error
}
```

**创建 Topic**：

```go
// 定义消息类型
type Event struct {
    Type    string
    Payload string
}

// 创建 Topic
topic := queue.NewTopic[Event](q, "events", &queue.TopicConfig{
    MaxRetries:  5,
    RetryDelay:  time.Second,
    MessageTTL:  24 * time.Hour,
})

// 发布简单消息
err := topic.Pub(Event{Type: "user.login", Payload: "john"})

// 批量发布
events := []Event{
    {Type: "e1", Payload: "data1"},
    {Type: "e2", Payload: "data2"},
}
err := topic.PubBatch(events)

// 发布带元数据的消息
msg := queue.NewMessage(Event{Type: "timeout", Payload: "data"})
msg.SetExpires(30 * time.Minute) // 30 分钟后过期
msg.Attempts = 3
err := topic.PubMsg(msg)
```

### 2. 消费者 API（Channel 接口）

```go
type Channel[T any] interface {
    Name() string

    // 订阅消息（自动并发处理）
    Subscribe(handler Handler[T])

    // 手动获取消息
    Next() (*Message[T], error)                      // 阻塞等待
    TryNext(timeout time.Duration) (*Message[T], error) // 超时等待

    // 消息确认
    Ack(msgId string) error  // 确认消息已处理
    Nack(msgId string) error // 消息处理失败，重新入队

    // 状态查询
    Depth() (int64, error) // 返回队列深度（待处理+未确认）

    // 生命周期
    Close() error
}
```

**创建 Channel**：

```go
// 获取或创建 Channel
ch, err := topic.GetOrAddChannel("handlers", &queue.ChannelConfig{
    MaxRetries:  5,
    RetryDelay:  time.Second,
    MaxInFlight: 10,       // 最大并发数
    AckTimeout:  30 * time.Second,
})
```

### 3. 消息处理（Handler）

```go
// Handler 类型定义
type Handler[T any] func(msg *Message[T]) (ProcessRsp, error)

// ProcessRsp 控制处理行为
type ProcessRsp struct {
    Retry        bool // 是否重试（true = 重新入队）
    SkipAttempts bool // 跳过记录重试次数
}
```

**订阅方式一：自动处理（推荐）**

```go
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    // 处理消息
    err := processEvent(msg.Body)
    if err != nil {
        // 返回 Retry=true 会重新入队
        return queue.ProcessRsp{Retry: true}, nil
    }

    // 处理成功，不重试
    return queue.ProcessRsp{Retry: false}, nil
})
```

**订阅方式二：手动获取**

```go
for {
    msg, err := ch.Next() // 阻塞等待
    if err != nil {
        break
    }

    // 处理消息
    err = handleMessage(msg.Body)
    if err != nil {
        // 处理失败，重新入队
        ch.Nack(msg.Id)
        continue
    }

    // 处理成功，确认消息
    err = ch.Ack(msg.Id)
    if err != nil {
        log.Errorf("Ack failed: %v", err)
    }
}
```

**订阅方式三：带超时的手动获取**

```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

for {
    msg, err := ch.TryNext(5 * time.Second) // 等待 5 秒
    if err != nil {
        if errors.Is(err, queue.ErrNoMessage) {
            continue // 没有消息，继续等待
        }
        break // 其他错误，退出
    }

    // 处理消息...
}
```

### 4. Message 结构

```go
type Message[T any] struct {
    Id        string    // 消息唯一标识（ULID）
    Body      T         // 消息体（泛型）
    Timestamp int64     // 消息产生时间戳（Unix 秒）
    ExpiresAt int64     // 过期时间戳（0 = 永不过期）
    Attempts  int       // 消费尝试次数
    Channel   string    // 所属 Channel 名称
}
```

**消息工具方法**：

```go
// 创建新消息
msg := queue.NewMessage(Event{Type: "test"})

// 使用指定 ID 创建消息
msg := queue.NewMessageWithID("custom-id", Event{Type: "test"})

// 克隆消息（用于不同 Channel）
msgCopy := msg.Clone()

// 设置过期时间（相对时间）
msg.SetExpires(30 * time.Minute) // 30 分钟后过期
msg.SetExpires(0)                 // 永不过期

// 设置过期时间（绝对时间戳）
msg.SetExpiresAt(time.Now().Add(24 * time.Hour).Unix())

// 检查是否过期
if msg.IsExpired() {
    // 消息已过期
}

// 获取剩余 TTL
ttl := msg.GetTTL() // 返回剩余秒数，-1 = 永不过期，0 = 已过期

// 重置尝试次数
msg.ResetAttempts()

// 增加尝试次数
msg.IncrementAttempts()
```

## 消息模式

### 1. 发布订阅模式（Pub-Sub）

一个 Topic 发布消息，多个 Channel 独立消费：

```go
// 创建一个 Topic
topic := queue.NewTopic[Event](q, "events", nil)

// 创建多个 Channel（消费者）
ch1, _ := topic.GetOrAddChannel("consumer-1", nil)
ch2, _ := topic.GetOrAddChannel("consumer-2", nil)

// 发布一条消息
topic.Pub(Event{Type: "test"})

// 两个 Channel 都会收到这条消息
ch1.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    fmt.Println("Consumer 1 received:", msg.Body.Type)
    return queue.ProcessRsp{Retry: false}, nil
})

ch2.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    fmt.Println("Consumer 2 received:", msg.Body.Type)
    return queue.ProcessRsp{Retry: false}, nil
})
```

### 2. 点对点模式（Peer-to-Peer）

多个消费者组内竞争消费（通过消费者组实现）：

```go
// Redis Streams 或 Kafka 自动支持
// 同一个消费者组内的消费者竞争消费消息

// 创建 Topic
topic := queue.NewTopic[Event](q, "tasks", nil)

// 同一个 Channel 的多个订阅者会竞争消费
ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
    MaxInFlight: 5, // 最多 5 个并发消费者
})

// 消息只会被一个消费者处理
for i := 0; i < 3; i++ {
    go ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
        fmt.Printf("Worker %d processing task\n", i)
        return queue.ProcessRsp{Retry: false}, nil
    })
}
```

### 3. 广播模式

所有 Channel 都收到所有消息（默认行为）：

```go
// 默认情况下，Topic 发布的消息会复制到所有 Channel
ch1, _ := topic.GetOrAddChannel("logger", nil)
ch2, _ := topic.GetOrAddChannel("metrics", nil)
ch3, _ := topic.GetOrAddChannel("audit", nil)

// 每条消息都会被三个 Channel 消费
topic.Pub(Event{Type: "important.event"})
```

## 重试机制

### 基础重试

```go
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    err := processEvent(msg.Body)
    if err != nil {
        // 处理失败，重新入队
        return queue.ProcessRsp{Retry: true}, nil
    }
    return queue.ProcessRsp{Retry: false}, nil
})
```

### 限制重试次数

```go
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    err := processEvent(msg.Body)
    if err != nil {
        if msg.Attempts < ch.config.MaxRetries {
            // 未超过最大重试次数，重新入队
            return queue.ProcessRsp{Retry: true}, nil
        }
        // 超过最大重试次数，放弃重试
        log.Errorf("Max retries exceeded for message %s", msg.Id)
        return queue.ProcessRsp{Retry: false}, nil
    }
    return queue.ProcessRsp{Retry: false}, nil
})
```

### 重试延迟

```go
// Channel 配置中设置重试延迟
ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
    RetryDelay: 5 * time.Second, // 每次重试前等待 5 秒
})
```

### 手动 Nack 重试

```go
msg, _ := ch.Next()
err := processMessage(msg.Body)
if err != nil {
    // 处理失败，重新入队
    ch.Nack(msg.Id)
} else {
    // 处理成功，确认消息
    ch.Ack(msg.Id)
}
```

## 延迟队列

### 设置消息过期时间

```go
// 方式一：相对时间
msg := queue.NewMessage(Event{Type: "delayed"})
msg.SetExpires(30 * time.Minute) // 30 分钟后过期
topic.PubMsg(msg)

// 方式二：绝对时间
msg := queue.NewMessage(Event{Type: "delayed"})
msg.SetExpiresAt(time.Now().Add(1 * time.Hour).Unix())
topic.PubMsg(msg)
```

### 消费者自动过滤过期消息

```go
// 消费者在获取消息时会自动检查过期
// 过期消息会被自动确认（Ack），不会传递给 Handler
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    // 这里的消息保证未过期
    fmt.Println("Processing non-expired message")
    return queue.ProcessRsp{Retry: false}, nil
})
```

### 检查消息是否过期

```go
if msg.IsExpired() {
    // 消息已过期
    ch.Ack(msg.Id) // 确认过期消息
    return
}
```

## 批量操作

### 批量发布

```go
// 方式一：批量发布简单消息
events := []Event{
    {Type: "e1", Payload: "data1"},
    {Type: "e2", Payload: "data2"},
    {Type: "e3", Payload: "data3"},
}
err := topic.PubBatch(events)

// 方式二：批量发布完整消息
msgs := []*queue.Message[Event]{
    queue.NewMessage(Event{Type: "e1"}),
    queue.NewMessage(Event{Type: "e2"}),
    queue.NewMessage(Event{Type: "e3"}),
}
err := topic.PubMsgBatch(msgs)
```

### 批量消费（并发控制）

```go
// MaxInFlight 控制并发消费数
ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
    MaxInFlight: 10, // 最多 10 个并发消费者
})

// Subscribe 内部使用 worker pool 实现并发控制
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    // 最多 10 个 goroutine 同时执行
    processEvent(msg.Body)
    return queue.ProcessRsp{Retry: false}, nil
})
```

### Redis Streams 批量读取

Redis Streams 使用 XREADGROUP，可配置 Count 参数：

```go
// 在 Redis 实现中
result, err := cli.XReadGroup(ctx, &redis.XReadGroupArgs{
    Group:    ch.group,
    Consumer: consumer,
    Streams:  []string{ch.stream, ">"},
    Count:    10, // 每次最多读取 10 条消息
    Block:    60 * time.Second,
}).Result()
```

### Kafka 批量写入

```go
// Kafka Writer 配置批量写入
writer := &kafka.Writer{
    Addr:         kafka.TCP(brokers...),
    Topic:        topic,
    BatchSize:    100,              // 批量大小
    BatchTimeout: 10 * time.Millisecond,
    BatchBytes:   1048576,         // 1MB
}
```

## 完整使用示例

### 示例 1：内存队列 - 基础发布订阅

```go
package main

import (
    "fmt"
    "time"

    "github.com/lazygophers/lrpc/middleware/storage/queue"
)

type Event struct {
    Type    string
    Payload string
}

func main() {
    // 创建内存队列
    q := queue.NewQueue(&queue.Config{
        StorageType: queue.StorageMemory,
    })
    defer q.Close()

    // 创建 Topic
    topic := queue.NewTopic[Event](q, "events", &queue.TopicConfig{
        MaxRetries: 3,
        RetryDelay: time.Second,
    })

    // 创建 Channel
    ch, _ := topic.GetOrAddChannel("handlers", &queue.ChannelConfig{
        MaxInFlight: 5,
    })

    // 订阅消息
    ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
        fmt.Printf("Received event: %s, Payload: %s\n", msg.Body.Type, msg.Body.Payload)
        return queue.ProcessRsp{Retry: false}, nil
    })

    // 发布消息
    for i := 0; i < 5; i++ {
        err := topic.Pub(Event{
            Type:    fmt.Sprintf("event.%d", i),
            Payload: fmt.Sprintf("data-%d", i),
        })
        if err != nil {
            fmt.Printf("Publish error: %v\n", err)
        }
        time.Sleep(100 * time.Millisecond)
    }

    // 等待消息处理完成
    time.Sleep(2 * time.Second)
}
```

### 示例 2：Redis Streams - 持久化队列

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/lazygophers/lrpc/middleware/storage/queue"
    "github.com/redis/go-redis/v9"
)

type Task struct {
    ID   int
    Data string
}

func main() {
    // 创建 Redis 客户端
    client := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
        DB:   0,
    })
    defer client.Close()

    // 测试连接
    ctx := context.Background()
    _, err := client.Ping(ctx).Result()
    if err != nil {
        panic(fmt.Sprintf("Redis connection failed: %v", err))
    }

    // 创建 Redis 队列
    q := queue.NewQueue(&queue.Config{
        StorageType: queue.StorageRedis,
        RedisConfig: &queue.RedisConfig{
            Addr:      "localhost:6379",
            KeyPrefix: "myapp:queue:",
        },
    })
    defer q.Close()

    // 创建 Topic
    topic := queue.NewTopic[Task](q, "tasks", &queue.TopicConfig{
        MaxRetries:  5,
        RetryDelay:  2 * time.Second,
        MessageTTL:  24 * time.Hour,
    })

    // 创建 Channel
    ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
        MaxInFlight: 10,
        AckTimeout:  30 * time.Second,
    })

    // 订阅消息
    ch.Subscribe(func(msg *queue.Message[Task]) (queue.ProcessRsp, error) {
        fmt.Printf("Processing task %d: %s (Attempt %d)\n",
            msg.Body.ID, msg.Body.Data, msg.Attempts)

        // 模拟处理
        time.Sleep(100 * time.Millisecond)

        // 模拟 30% 失败率
        if msg.Body.ID%10 == 3 {
            fmt.Printf("Task %d failed, retrying...\n", msg.Body.ID)
            return queue.ProcessRsp{Retry: true}, nil
        }

        return queue.ProcessRsp{Retry: false}, nil
    })

    // 发布任务
    for i := 0; i < 20; i++ {
        err := topic.Pub(Task{
            ID:   i,
            Data: fmt.Sprintf("task-data-%d", i),
        })
        if err != nil {
            fmt.Printf("Publish error: %v\n", err)
        }
    }

    // 等待处理完成
    time.Sleep(5 * time.Second)

    // 查询队列深度
    depth, _ := ch.Depth()
    fmt.Printf("Queue depth: %d\n", depth)
}
```

### 示例 3：Kafka - 分布式高吞吐队列

```go
package main

import (
    "fmt"
    "time"

    "github.com/lazygophers/lrpc/middleware/storage/queue"
)

type OrderEvent struct {
    OrderID   string
    EventType string
    Amount    float64
}

func main() {
    // 创建 Kafka 队列
    q := queue.NewQueue(&queue.Config{
        StorageType: queue.StorageKafka,
        KafkaConfig: &queue.KafkaConfig{
            Brokers:            []string{"localhost:9092"},
            TopicPrefix:        "orders-",
            Partition:          3,
            ReplicationFactor:  2,
            AutoCreateTopics:   true,
            CompressionType:    "gzip",
            RequiredAcks:       1,
            ReadBatchTimeout:   10 * time.Second,
            WriteTimeout:       10 * time.Second,
        },
    })
    defer q.Close()

    // 创建 Topic
    topic := queue.NewTopic[OrderEvent](q, "events", &queue.TopicConfig{
        MaxRetries: 5,
    })

    // 创建 Channel（订单处理器）
    orderProcessor, _ := topic.GetOrAddChannel("order-processor", &queue.ChannelConfig{
        MaxInFlight: 20,
    })

    // 订阅订单事件
    orderProcessor.Subscribe(func(msg *queue.Message[OrderEvent]) (queue.ProcessRsp, error) {
        event := msg.Body

        switch event.EventType {
        case "order.created":
            fmt.Printf("Processing new order: %s, Amount: %.2f\n", event.OrderID, event.Amount)
            // 处理新订单逻辑

        case "order.paid":
            fmt.Printf("Order paid: %s\n", event.OrderID)
            // 处理支付逻辑

        case "order.shipped":
            fmt.Printf("Order shipped: %s\n", event.OrderID)
            // 处理发货逻辑
        }

        return queue.ProcessRsp{Retry: false}, nil
    })

    // 创建 Channel（审计日志）
    auditLogger, _ := topic.GetOrAddChannel("audit-logger", &queue.ChannelConfig{
        MaxInFlight: 5,
    })

    // 订阅审计日志
    auditLogger.Subscribe(func(msg *queue.Message[OrderEvent]) (queue.ProcessRsp, error) {
        fmt.Printf("[AUDIT] Event: %s, Order: %s, Amount: %.2f\n",
            msg.Body.EventType, msg.Body.OrderID, msg.Body.Amount)
        return queue.ProcessRsp{Retry: false}, nil
    })

    // 模拟发布订单事件
    events := []OrderEvent{
        {OrderID: "ORD-001", EventType: "order.created", Amount: 99.99},
        {OrderID: "ORD-001", EventType: "order.paid", Amount: 99.99},
        {OrderID: "ORD-002", EventType: "order.created", Amount: 149.99},
        {OrderID: "ORD-001", EventType: "order.shipped", Amount: 99.99},
    }

    for _, event := range events {
        err := topic.Pub(event)
        if err != nil {
            fmt.Printf("Publish error: %v\n", err)
        }
        time.Sleep(100 * time.Millisecond)
    }

    // 等待处理完成
    time.Sleep(3 * time.Second)
}
```

### 示例 4：手动消费模式

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/lazygophers/lrpc/middleware/storage/queue"
)

type Job struct {
    ID   int
    Work string
}

func main() {
    q := queue.NewQueue(&queue.Config{
        StorageType: queue.StorageMemory,
    })
    defer q.Close()

    topic := queue.NewTopic[Job](q, "jobs", nil)
    ch, _ := topic.GetOrAddChannel("worker", &queue.ChannelConfig{
        MaxInFlight: 1,
    })

    // 发布任务
    for i := 0; i < 5; i++ {
        topic.Pub(Job{ID: i, Work: fmt.Sprintf("work-%d", i)})
    }

    // 手动消费
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    for {
        select {
        case <-ctx.Done():
            fmt.Println("Timeout, exiting...")
            return

        default:
            // 尝试获取消息（带超时）
            msg, err := ch.TryNext(1 * time.Second)
            if err != nil {
                if queue.IsErrNoMessage(err) {
                    continue // 没有消息，继续等待
                }
                fmt.Printf("Error: %v\n", err)
                return
            }

            // 处理消息
            fmt.Printf("Processing job %d: %s\n", msg.Body.ID, msg.Body.Work)
            time.Sleep(500 * time.Millisecond)

            // 确认消息
            if err := ch.Ack(msg.Id); err != nil {
                fmt.Printf("Ack error: %v\n", err)
            }
        }
    }
}

// IsErrNoMessage 检查是否是"没有消息"错误
func IsErrNoMessage(err error) bool {
    return err != nil && err.Error() == "no message available"
}
```

## 配置说明

### Queue 全局配置

```go
type Config struct {
    StorageType StorageType   // 存储类型：memory/redis/kafka
    MaxRetries  int           // 最大重试次数（默认 5）
    RetryDelay  time.Duration // 重试延迟（默认 1s）
    MessageTTL  time.Duration // 消息过期时间（默认 24h）
    MaxBodySize int64         // 最大消息体大小（默认 1MB）
    MaxMsgSize  int64         // 最大消息数量（默认 1000000）

    // Redis 专用
    RedisConfig *RedisConfig
    RedisClient *redis.Client

    // Kafka 专用
    KafkaConfig *KafkaConfig
}
```

### Redis 配置

```go
type RedisConfig struct {
    Addr         string        // 服务器地址（默认 localhost:6379）
    Password     string        // 密码
    DB           int           // 数据库编号（默认 0）
    KeyPrefix    string        // 键名前缀（默认 lrpc:queue:）
    PoolSize     int           // 连接池大小（默认 10）
    MinIdleConns int           // 最小空闲连接（默认 5）
    MaxRetries   int           // 最大重试次数（默认 3）
    DialTimeout  time.Duration // 连接超时（默认 5s）
    ReadTimeout  time.Duration // 读取超时（默认 3s）
    WriteTimeout time.Duration // 写入超时（默认 3s）
    PoolTimeout  time.Duration // 连接池超时（默认 4s）
}
```

### Kafka 配置

```go
type KafkaConfig struct {
    Brokers            []string      // 服务器地址列表
    TopicPrefix        string        // Topic 前缀（默认 lrpc-queue-）
    Partition          int           // 分区数（默认 1）
    ReplicationFactor  int           // 副本因子（默认 1）
    ConsumerGroupID    string        // 消费者组 ID
    AutoCreateTopics   bool          // 自动创建 Topic（默认 true）
    ReadBatchTimeout   time.Duration // 批量读取超时（默认 10s）
    WriteTimeout       time.Duration // 写入超时（默认 10s）
    RequiredAcks       int           // 确认级别：0/1/-1（默认 1）
    CompressionType    string        // 压缩类型：none/gzip/snappy/lz4/zstd
    SessionTimeout     time.Duration // 会话超时（默认 30s）
    RebalanceTimeout   time.Duration // 重平衡超时（默认 60s）
    CommitInterval     time.Duration // 提交间隔（默认 1s）
    HeartbeatInterval  time.Duration // 心跳间隔（默认 3s）
    MaxAttempts        int           // 最大消费尝试次数（默认 5）
    DialTimeout        time.Duration // 连接超时（默认 10s）
}
```

### Topic 配置

```go
type TopicConfig struct {
    MaxRetries  int           // 最大重试次数（默认 5）
    RetryDelay  time.Duration // 重试延迟（默认 1s）
    MessageTTL  time.Duration // 消息过期时间（默认 24h）
    MaxBodySize int64         // 最大消息体大小（默认 1MB）
    MaxMsgSize  int64         // 最大消息数量（默认 1000000）
}
```

### Channel 配置

```go
type ChannelConfig struct {
    MaxRetries  int           // 最大重试次数（默认 5）
    RetryDelay  time.Duration // 重试延迟（默认 1s）
    MessageTTL  time.Duration // 消息过期时间（默认 24h）
    MaxInFlight int           // 最大并发数（默认 10）
    AckTimeout  time.Duration // 确认超时（默认 30s）
}
```

## 最佳实践

### 1. 选择合适的存储后端

| 场景 | 推荐后端 | 原因 |
|------|---------|------|
| 单元测试、开发环境 | Memory | 最快性能，无需外部依赖 |
| 单机生产环境 | Redis Streams | 持久化、简单、性能好 |
| 分布式生产环境 | Kafka | 高吞吐、分区、水平扩展 |

### 2. 合理配置 MaxInFlight

```go
// 根据处理能力设置并发数
// 值太小：吞吐量低
// 值太大：内存压力大、可能导致消息积压

// CPU 密集型任务
ch, _ := topic.GetOrAddChannel("cpu-workers", &queue.ChannelConfig{
    MaxInFlight: runtime.NumCPU(), // 等于 CPU 核数
})

// IO 密集型任务
ch, _ := topic.GetOrAddChannel("io-workers", &queue.ChannelConfig{
    MaxInFlight: runtime.NumCPU() * 2, // CPU 核数的 2 倍
})
```

### 3. 设置消息过期时间

```go
// 避免无限重试导致消息堆积
topic := queue.NewTopic[Event](q, "events", &queue.TopicConfig{
    MessageTTL: 24 * time.Hour, // 消息 24 小时后过期
})

// 或在发布时设置过期时间
msg := queue.NewMessage(event)
msg.SetExpires(30 * time.Minute) // 30 分钟后过期
topic.PubMsg(msg)
```

### 4. 处理 Panic

```go
// Handler 内部已通过 runtime.CachePanicWithHandle 处理 panic
// 但建议在 Handler 内部也处理 panic

ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    defer func() {
        if r := recover(); r != nil {
            log.Errorf("Panic in handler: %v", r)
        }
    }()

    // 处理逻辑...
    return queue.ProcessRsp{Retry: false}, nil
})
```

### 5. 资源管理

```go
// 总是使用 defer 关闭资源
func processQueue() {
    q := queue.NewQueue(&queue.Config{StorageType: queue.StorageMemory})
    defer q.Close() // 确保队列关闭

    topic := queue.NewTopic[Event](q, "events", nil)
    defer topic.Close() // 确保主题关闭

    ch, _ := topic.GetOrAddChannel("workers", nil)
    defer ch.Close() // 确保通道关闭

    // 处理逻辑...
}
```

### 6. 监控队列深度

```go
// 定期检查队列深度，及时发现积压
go func() {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for range ticker.C {
        depth, err := ch.Depth()
        if err != nil {
            log.Errorf("Failed to get depth: %v", err)
            continue
        }

        if depth > 1000 {
            log.Warnf("Queue depth is high: %d", depth)
            // 发送告警...
        }
    }
}()
```

### 7. 错误处理

```go
ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
    err := processEvent(msg.Body)
    if err != nil {
        // 根据错误类型决定是否重试
        if isTransientError(err) {
            // 临时错误，重试
            return queue.ProcessRsp{Retry: true}, nil
        } else {
            // 永久错误，不重试
            log.Errorf("Permanent error processing message %s: %v", msg.Id, err)
            return queue.ProcessRsp{Retry: false}, nil
        }
    }

    return queue.ProcessRsp{Retry: false}, nil
})

func isTransientError(err error) bool {
    // 判断是否是临时错误（网络超时、服务不可用等）
    return errors.Is(err, context.DeadlineExceeded) ||
           errors.Is(err, context.Canceled)
}
```

### 8. 使用消费者组实现负载均衡

```go
// Redis Streams 和 Kafka 原生支持消费者组
// 同一个消费者组内的消费者会自动分担消息负载

// 多个进程/实例使用相同的消费者组配置
for i := 0; i < 3; i++ {
    go func(workerID int) {
        // 每个 worker 使用独立的消费者实例
        ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
            MaxInFlight: 5,
        })

        ch.Subscribe(func(msg *queue.Message[Event]) (queue.ProcessRsp, error) {
            fmt.Printf("Worker %d processing message %s\n", workerID, msg.Id)
            return queue.ProcessRsp{Retry: false}, nil
        })
    }(i)
}
```

## 常见问题

### 1. 消息丢失怎么办？

**Memory Queue**：进程重启会丢失所有消息，建议仅用于测试。

**Redis Streams**：配置 `MaxLen` 限制队列长度，旧消息会被自动删除。

**Kafka**：配置合适的 `Retention` 策略，避免消息被过早删除。

```go
// Redis Streams 配置最大消息数
topic := queue.NewTopic[Event](q, "events", &queue.TopicConfig{
    MaxMsgSize: 1000000, // 最多保留 100 万条消息
})
```

### 2. 如何保证消息顺序？

**Memory Queue**：单个 Channel 内保证顺序。

**Redis Streams**：单个消费者组内保证顺序（使用 `XREADGROUP`）。

**Kafka**：单个分区内保证顺序。

```go
// Kafka 配置单个分区，保证顺序
q := queue.NewQueue(&queue.Config{
    StorageType: queue.StorageKafka,
    KafkaConfig: &queue.KafkaConfig{
        Partition: 1, // 单分区保证顺序
    },
})
```

### 3. 如何处理消息积压？

- 增加消费者数量（水平扩展）
- 增大 `MaxInFlight` 提高并发
- 优化消息处理逻辑
- 增加分区数量（Kafka）

```go
// 增加并发
ch, _ := topic.GetOrAddChannel("workers", &queue.ChannelConfig{
    MaxInFlight: 50, // 增加到 50
})
```

### 4. 如何实现消息优先级？

当前版本不支持原生优先级队列。可以通过以下方式实现：

**方案一**：创建多个 Channel

```go
highPriorityCh, _ := topic.GetOrAddChannel("high-priority", &queue.ChannelConfig{
    MaxInFlight: 10, // 高优先级通道
})

lowPriorityCh, _ := topic.GetOrAddChannel("low-priority", &queue.ChannelConfig{
    MaxInFlight: 2, // 低优先级通道
})
```

**方案二**：在消息中添加优先级字段

```go
type PriorityMessage struct {
    Priority int
    Data     string
}

ch.Subscribe(func(msg *queue.Message[PriorityMessage]) (queue.ProcessRsp, error) {
    if msg.Body.Priority > 5 {
        // 高优先级消息立即处理
        processImmediately(msg.Body)
    } else {
        // 低优先级消息延迟处理
        time.Sleep(1 * time.Second)
        process(msg.Body)
    }
    return queue.ProcessRsp{Retry: false}, nil
})
```

## 后端对比

| 特性 | Memory | Redis Streams | Kafka |
|------|--------|---------------|-------|
| 持久化 | 否 | 是 | 是 |
| 分布式 | 否 | 是（主从） | 是（分区） |
| 消费者组 | 模拟 | 原生支持 | 原生支持 |
| 消息确认 | 内存 | Pending List | Offset |
| 消息重试 | 简单 | 完整支持 | 完整支持 |
| 分区支持 | 否 | 否 | 是 |
| 消息头 | 否 | 否 | 是 |
| 性能 | 极高 | 高 | 高 |
| 吞吐量 | 低 | 中 | 高 |
| 延迟 | 极低 | 低 | 中 |
| 部署复杂度 | 简单 | 简单 | 复杂 |
| 使用场景 | 测试、单机 | 中小规模 | 大规模生产 |

## 性能优化建议

### 1. 批量操作

```go
// 批量发布比单条发布效率高
events := make([]Event, 1000)
for i := range events {
    events[i] = Event{Type: fmt.Sprintf("event-%d", i)}
}
topic.PubBatch(events) // 批量发布
```

### 2. 调整 Kafka 批量配置

```go
KafkaConfig: &queue.KafkaConfig{
    // 增加 Writer 批量配置
    // BatchSize:    100,              // 在 kafka.go 中硬编码
    // BatchTimeout: 10 * time.Millisecond,
    // BatchBytes:   1048576,
}
```

### 3. Redis 连接池配置

```go
RedisConfig: &queue.RedisConfig{
    PoolSize:     50,  // 增加连接池大小
    MinIdleConns: 10,  // 增加最小空闲连接
    PoolTimeout:  10 * time.Second,
}
```

### 4. 消息压缩（Kafka）

```go
KafkaConfig: &queue.KafkaConfig{
    CompressionType: "zstd", // 使用 Zstandard 压缩
}
```

## 参考资源

- **GitHub**: https://github.com/lazygophers/lrpc
- **文档**: `/middleware/storage/queue/llms.txt`
- **Redis Streams**: https://redis.io/docs/data-types/streams/
- **go-redis**: https://redis.uptrace.dev/
- **Kafka**: https://kafka.apache.org/documentation/
- **kafka-go**: https://github.com/segmentio/kafka-go

## 版本要求

- **Go**: >= 1.22（泛型支持）
- **Redis**: >= 5.0（Streams 支持）
- **Kafka**: >= 2.0

## 依赖包

- `github.com/redis/go-redis/v9` - Redis 客户端
- `github.com/segmentio/kafka-go` - Kafka 客户端
- `github.com/lazygophers/utils/cryptox` - ULID 生成
- `github.com/lazygophers/utils/json` - JSON 序列化
- `github.com/lazygophers/utils/routine` - Goroutine 管理
- `github.com/lazygophers/log` - 日志
- `github.com/lazygophers/lrpc/middleware/xerror` - 错误处理
