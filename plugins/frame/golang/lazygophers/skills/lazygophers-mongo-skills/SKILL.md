---
name: lazygophers-mongo-skills
description: lrpc mongo MongoDB 数据库访问规范 - 提供统一的 MongoDB 访问抽象，支持 CRUD、聚合、事务和索引管理
---

# lazygophers-mongo - MongoDB 数据库访问

提供统一的 MongoDB 访问抽象层，支持文档操作、聚合查询、事务和索引管理。

## 特性

- 📦 **统一接口** - 简化 MongoDB 操作
- 🔍 **丰富查询** - 支持复杂查询条件
- 📊 **聚合管道** - 强大的数据分析能力
- 🔄 **多文档事务** - ACID 事务支持
- 🏷️ **索引管理** - 自动索引创建和优化
- 🔌 **连接池** - 自动管理连接
- ⚡ **高性能** - 批量操作、游标查询

## 基础使用

### 初始化连接

```go
import (
    "github.com/lazygophers/lrpc/middleware/storage/mongo"
)

// 创建客户端
client, err := mongo.New(mongo.Config{
    Host:     "localhost",
    Port:     27017,
    Database: "mydb",
    Username: "user",
    Password: "pass",
    // 连接池配置
    MinPoolSize: 10,
    MaxPoolSize: 100,
})

// 使用连接字符串
client, err := mongo.New(mongo.Config{
    URI: "mongodb://user:pass@localhost:27017/mydb",
})

// 副本集
client, err := mongo.New(mongo.Config{
    URI: "mongodb://localhost:27017,localhost:27018,localhost:27019/mydb?replicaSet=myReplicaSet",
})
```

### 注册中间件

```go
server := lrpc.NewServer()

// 创建中间件
mongoMiddleware := mongo.NewMiddleware(client)
server.Use(mongoMiddleware)

// 在 Handler 中使用
func Handler(ctx *lrpc.Context, db *mongo.DB) error {
    collection := db.Collection("users")
    // ...
}
```

## CRUD 操作

### 插入文档

```go
collection := db.Collection("users")

// 插入单个文档
user := bson.M{
    "name":  "John",
    "email": "john@example.com",
    "age":   30,
}

result, err := collection.InsertOne(ctx, user)
if err != nil {
    return err
}
fmt.Println("Inserted ID:", result.InsertedID)

// 批量插入
users := []interface{}{
    bson.M{"name": "John", "age": 30},
    bson.M{"name": "Jane", "age": 25},
    bson.M{"name": "Bob", "age": 35},
}

result, err := collection.InsertMany(ctx, users)
if err != nil {
    return err
}
fmt.Println("Inserted IDs:", result.InsertedIDs)
```

### 查询文档

```go
// 查询单个文档
var user bson.M
err := collection.FindOne(ctx, bson.M{"name": "John"}).Decode(&user)

// 查询多个文档
cursor, err := collection.Find(ctx, bson.M{"age": bson.M{"$gt": 18}})
if err != nil {
    return err
}
defer cursor.Close(ctx)

var users []bson.M
if err = cursor.All(ctx, &users); err != nil {
    return err
}
```

### 更新文档

```go
// 更新单个文档
filter := bson.M{"name": "John"}
update := bson.M{"$set": bson.M{"age": 31}}

result, err := collection.UpdateOne(ctx, filter, update)
if err != nil {
    return err
}
fmt.Println("Matched:", result.MatchedCount)
fmt.Println("Modified:", result.ModifiedCount)

// 更新多个文档
filter := bson.M{"status": "inactive"}
update := bson.M{"$set": bson.M{"status": "active"}}

result, err := collection.UpdateMany(ctx, filter, update)

// 替换文档
filter := bson.M{"name": "John"}
replacement := bson.M{"name": "Jane", "age": 25, "email": "jane@example.com"}

result, err := collection.ReplaceOne(ctx, filter, replacement)
```

### 删除文档

```go
// 删除单个文档
filter := bson.M{"name": "John"}
result, err := collection.DeleteOne(ctx, filter)
if err != nil {
    return err
}
fmt.Println("Deleted:", result.DeletedCount)

// 删除多个文档
filter := bson.M{"age": bson.M{"$lt": 18}}
result, err := collection.DeleteMany(ctx, filter)

// 删除集合
err := collection.Drop(ctx)
```

## 查询条件

### 比较操作符

```go
// $gt - 大于
filter := bson.M{"age": bson.M{"$gt": 18}}

// $gte - 大于等于
filter := bson.M{"age": bson.M{"$gte": 18}}

// $lt - 小于
filter := bson.M{"age": bson.M{"$lt": 65}}

// $lte - 小于等于
filter := bson.M{"age": bson.M{"$lte": 65}}

// $ne - 不等于
filter := bson.M{"status": bson.M{"$ne": "deleted"}}

// $in - 在数组中
filter := bson.M{"status": bson.M{"$in": []string{"active", "pending"}}}

// $nin - 不在数组中
filter := bson.M{"status": bson.M{"$nin": []string{"deleted", "banned"}}}
```

### 逻辑操作符

```go
// $and - 与
filter := bson.M{
    "$and": []bson.M{
        {"age": bson.M{"$gt": 18}},
        {"status": "active"},
    },
}

// $or - 或
filter := bson.M{
    "$or": []bson.M{
        {"status": "active"},
        {"status": "pending"},
    },
}

// $not - 非
filter := bson.M{
    "age": bson.M{"$not": bson.M{"$gt": 18}},
}

// $nor - 或非
filter := bson.M{
    "$nor": []bson.M{
        {"status": "deleted"},
        {"status": "banned"},
    },
}
```

### 数组操作符

```go
// $all - 包含所有
filter := bson.M{"tags": bson.M{"$all": []string{"golang", "mongo"}}}

// $size - 数组大小
filter := bson.M{"items": bson.M{"$size": 5}}

// $elemMatch - 数组元素匹配
filter := bson.M{
    "comments": bson.M{
        "$elemMatch": bson.M{
            "author": "John",
            "likes": bson.M{"$gt": 10},
        },
    },
}
```

### 字符串操作

```go
// 正则表达式
filter := bson.M{"name": bson.M{"$regex": "^John", "$options": "i"}}

// 使用正则表达式
regex := regexp.MustCompile("^John")
filter := bson.M{"name": bson.M{"$regex": regex}}
```

## 聚合查询

### 基础聚合

```go
// $match - 匹配
// $group - 分组
// $sort - 排序
// $limit - 限制
// $skip - 跳过

pipeline := mongo.Pipeline{
    bson.D{{"$match", bson.D{{"age", bson.D{{"$gt", 18}}}}}},
    bson.D{{"$group", bson.D{
        {"_id", "$status"},
        {"count", bson.D{{"$sum", 1}}},
        {"avg_age", bson.D{{"$avg", "$age"}}},
    }}},
    bson.D{{"$sort", bson.D{{"count", -1}}}},
    bson.D{{"$limit", 10}},
}

cursor, err := collection.Aggregate(ctx, pipeline)
if err != nil {
    return err
}
defer cursor.Close(ctx)

var results []bson.M
cursor.All(ctx, &results)
```

### 常用聚合阶段

```go
// $project - 投影
pipeline := mongo.Pipeline{
    bson.D{{"$project", bson.D{
        {"name", 1},
        {"email", 1},
        {"age", 1},
    }}},
}

// $lookup - 左连接
pipeline := mongo.Pipeline{
    bson.D{{"$lookup", bson.D{
        {"from", "orders"},
        {"localField", "_id"},
        {"foreignField", "user_id"},
        {"as", "orders"},
    }}},
}

// $unwind - 展开数组
pipeline := mongo.Pipeline{
    bson.D{{"$unwind", "$tags"}},
}

// $addFields - 添加字段
pipeline := mongo.Pipeline{
    bson.D{{"$addFields", bson.D{
        {"full_name", bson.D{{"$concat", []string{"$name.first", " ", "$name.last"}}}},
    }}},
}

// $facet - 多面聚合
pipeline := mongo.Pipeline{
    bson.D{{"$facet", bson.D{
        {"active", bson.A{
            bson.D{{"$match", bson.D{{"status", "active"}}}},
            bson.D{{"$count", "total"}},
        }},
        {"inactive", bson.A{
            bson.D{{"$match", bson.D{{"status", "inactive"}}}},
            bson.D{{"$count", "total"}},
        }},
    }}},
}
```

### 聚合示例

```go
// 统计各状态用户数量
pipeline := mongo.Pipeline{
    bson.D{{"$group", bson.D{
        {"_id", "$status"},
        {"count", bson.D{{"$sum", 1}}},
    }}},
    bson.D{{"$sort", bson.D{{"count", -1}}}},
}

// 查找活跃用户及其订单数量
pipeline := mongo.Pipeline{
    bson.D{{"$match", bson.D{{"status", "active"}}}},
    bson.D{{"$lookup", bson.D{
        {"from", "orders"},
        {"localField", "_id"},
        {"foreignField", "user_id"},
        {"as", "orders"},
    }}},
    bson.D{{"$addFields", bson.D{
        {"order_count", bson.D{{"$size", "$orders"}}},
    }}},
    bson.D{{"$project", bson.D{
        {"name", 1},
        {"email", 1},
        {"order_count", 1},
    }}},
}

// 时间序列统计
pipeline := mongo.Pipeline{
    bson.D{{"$group", bson.D{
        {"_id", bson.D{
            {"year", bson.D{{"$year", "$created_at"}}},
            {"month", bson.D{{"$month", "$created_at"}}},
            {"day", bson.D{{"$dayOfMonth", "$created_at"}}},
        }},
        {"count", bson.D{{"$sum", 1}}},
    }}},
    bson.D{{"$sort", bson.D{{"_id", 1}}}},
}
```

## 索引管理

### 创建索引

```go
// 单字段索引
indexModel := mongo.IndexModel{
    Keys: bson.D{{"email", 1}},
}
name, err := collection.Indexes().CreateOne(ctx, indexModel)

// 复合索引
indexModel = mongo.IndexModel{
    Keys: bson.D{
        {"status", 1},
        {"created_at", -1},
    },
}
name, err = collection.Indexes().CreateOne(ctx, indexModel)

// 唯一索引
indexModel = mongo.IndexModel{
    Keys:    bson.D{{"email", 1}},
    Options: options.Index().SetUnique(true),
}
name, err = collection.Indexes().CreateOne(ctx, indexModel)

// 稀疏索引
indexModel = mongo.IndexModel{
    Keys:    bson.D{{"phone", 1}},
    Options: options.Index().SetSparse(true),
}
name, err = collection.Indexes().CreateOne(ctx, indexModel)

// TTL 索引（自动过期）
indexModel = mongo.IndexModel{
    Keys:    bson.D{{"created_at", 1}},
    Options: options.Index().SetExpireAfterSeconds(3600),
}
name, err = collection.Indexes().CreateOne(ctx, indexModel)

// 文本索引
indexModel = mongo.IndexModel{
    Keys: bson.D{{"content", "text"}},
    Options: options.Index().
        SetWeights(map[string]int32{"title": 10, "content": 1}),
}
name, err = collection.Indexes().CreateOne(ctx, indexModel)
```

### 查看索引

```go
// 列出所有索引
cursor, err := collection.Indexes().List(ctx)
if err != nil {
    return err
}

var indexes []bson.M
if err = cursor.All(ctx, &indexes); err != nil {
    return err
}

for _, index := range indexes {
    fmt.Println("Index:", index)
}
```

### 删除索引

```go
// 删除单个索引
err := collection.Indexes().DropOne(ctx, "email_1")

// 删除所有索引（除了 _id）
err := collection.Indexes().DropAll(ctx)
```

## 事务处理

### 会话事务

```go
// 创建会话
session, err := client.StartSession()
if err != nil {
    return err
}
defer session.EndSession(ctx)

// 开启事务
err = mongo.WithSession(ctx, session, func(sc mongo.SessionContext) error {
    // 开始事务
    if err := session.StartTransaction(); err != nil {
        return err
    }

    // 执行操作
    if _, err := db.Collection("users").InsertOne(sc, user); err != nil {
        session.AbortTransaction(sc)
        return err
    }

    if _, err := db.Collection("orders").InsertOne(sc, order); err != nil {
        session.AbortTransaction(sc)
        return err
    }

    // 提交事务
    if err := session.CommitTransaction(sc); err != nil {
        return err
    }

    return nil
})
```

### 回调事务

```go
// 使用回调简化事务
err = mongo.WithSession(ctx, session, func(sc mongo.SessionContext) error {
    return mongo.WithTransaction(sc, func(sc mongo.SessionContext) error {
        // 执行操作
        if _, err := db.Collection("users").InsertOne(sc, user); err != nil {
            return err
        }

        if _, err := db.Collection("orders").InsertOne(sc, order); err != nil {
            return err
        }

        return nil
    })
})
```

## 分页查询

### 基础分页

```go
type PageResult struct {
    Total int64       `json:"total"`
    Page  int         `json:"page"`
    Size  int         `json:"size"`
    Data  interface{} `json:"data"`
}

func GetUsers(db *mongo.Database, page, size int) (*PageResult, error) {
    collection := db.Collection("users")
    ctx := context.Background()

    // 查询总数
    total, err := collection.CountDocuments(ctx, bson.M{})
    if err != nil {
        return nil, err
    }

    // 查询数据
    skip := (page - 1) * size
    cursor, err := collection.Find(ctx,
        bson.M{},
        options.Find().SetSkip(int64(skip)).SetLimit(int64(size)),
    )
    if err != nil {
        return nil, err
    }
    defer cursor.Close(ctx)

    var users []bson.M
    if err = cursor.All(ctx, &users); err != nil {
        return nil, err
    }

    return &PageResult{
        Total: total,
        Page:  page,
        Size:  size,
        Data:  users,
    }, nil
}
```

## 最佳实践

### 1. 使用上下文超时

```go
// ✅ 带超时的查询
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

cursor, err := collection.Find(ctx, filter)

// ❌ 没有超时控制
cursor, err := collection.Find(context.Background(), filter)
```

### 2. 批量操作

```go
// ✅ 使用批量写入
models := []mongo.WriteModel{
    mongo.NewInsertOneModel().SetDocument(user1),
    mongo.NewInsertOneModel().SetDocument(user2),
    mongo.NewInsertOneModel().SetDocument(user3),
}

result, err := collection.BulkWrite(ctx, models)

// ❌ 逐个插入
for _, user := range users {
    collection.InsertOne(ctx, user)
}
```

### 3. 索引优化

```go
// ✅ 为常用查询字段创建索引
indexModel := mongo.IndexModel{
    Keys: bson.D{{"status", 1}, {"created_at", -1}},
}
collection.Indexes().CreateOne(ctx, indexModel)

// ✅ 使用投影减少返回字段
opts := options.Find().SetProjection(bson.M{
    "name": 1,
    "email": 1,
})
cursor, err := collection.Find(ctx, filter, opts)
```

### 4. 使用结构体

```go
// ✅ 使用结构体而非 bson.M
type User struct {
    ID      primitive.ObjectID `bson:"_id"`
    Name    string             `bson:"name"`
    Email   string             `bson:"email"`
    Age     int                `bson:"age"`
    Created time.Time          `bson:"created_at"`
}

var user User
collection.FindOne(ctx, filter).Decode(&user)

// ❌ 使用 map 类型不安全
var user bson.M
collection.FindOne(ctx, filter).Decode(&user)
```

## 参考资源

- [lazygophers/lrpc mongo](https://github.com/lazygophers/lrpc/tree/master/middleware/storage/mongo)
- [MongoDB Go Driver](https://github.com/mongodb/mongo-go-driver)
- [MongoDB 文档](https://www.mongodb.com/docs/)
