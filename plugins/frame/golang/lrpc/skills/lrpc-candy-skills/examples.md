# candy 模块使用示例

本文档提供了 lazygophers/utils candy 模块的实用示例，帮助开发者快速上手。

## 目录

1. [类型转换](#1-类型转换)
2. [切片操作](#2-切片操作)
3. [集合操作](#3-集合操作)
4. [结构体操作](#4-结构体操作)
5. [反射与深度操作](#5-反射与深度操作)
6. [实际应用场景](#6-实际应用场景)

---

## 1. 类型转换

### 1.1 基础类型转换

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

func main() {
    // 字符串转整数
    age := candy.ToInt("25")        // 25
    price := candy.ToInt64("99")    // 99

    // 数字转字符串
    str := candy.ToString(42)       // "42"
    floatStr := candy.ToString(3.14) // "3.14"

    // 布尔值转换
    flag := candy.ToBool("yes")     // true
    flag = candy.ToBool(1)          // true
    flag = candy.ToBool(0)          // false

    // 指针创建
    ptr := candy.ToPtr(42)          // *int

    fmt.Printf("Age: %d, Price: %d, String: %s, Flag: %v\n",
        age, price, str, flag)
}
```

### 1.2 配置值转换

```go
// 从环境变量或配置文件读取值的实用模式
func getConfig() (timeout int, enabled bool, rate float64) {
    // 模拟配置数据
    config := map[string]interface{}{
        "timeout": "30",
        "enabled": "true",
        "rate":    "1.5",
    }

    timeout = candy.ToInt(config["timeout"])
    enabled = candy.ToBool(config["enabled"])
    rate = candy.ToFloat64(config["rate"])

    return
}
```

---

## 2. 切片操作

### 2.1 过滤与转换

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

type User struct {
    ID    int
    Name  string
    Age   int
    Email string
}

func main() {
    users := []User{
        {ID: 1, Name: "Alice", Age: 25, Email: "alice@example.com"},
        {ID: 2, Name: "Bob", Age: 17, Email: "bob@example.com"},
        {ID: 3, Name: "Charlie", Age: 30, Email: "charlie@example.com"},
        {ID: 4, Name: "Diana", Age: 28, Email: "diana@example.com"},
    }

    // 筛选成年用户
    adults := candy.Filter(users, func(u User) bool {
        return u.Age >= 18
    })

    // 提取姓名
    names := candy.Map(adults, func(u User) string {
        return u.Name
    })

    fmt.Printf("Adults: %v\n", names)
    // 输出: Adults: [Alice Charlie Diana]
}
```

### 2.2 数据聚合

```go
// 计算平均年龄
func averageAge(users []User) float64 {
    if len(users) == 0 {
        return 0
    }

    ages := candy.Map(users, func(u User) int {
        return u.Age
    })

    total := candy.Sum(ages...)
    return float64(total) / float64(len(users))
}

// 查找最大/最小年龄
func ageRange(users []User) (min, max int) {
    ages := candy.Map(users, func(u User) int {
        return u.Age
    })

    return candy.Min(ages...), candy.Max(ages...)
}
```

### 2.3 切片重组

```go
// 去重
uniqueIDs := candy.Unique([]int{1, 2, 2, 3, 3, 3, 4})
// 结果: [1, 2, 3, 4]

// 反转
reversed := candy.Reverse([]int{1, 2, 3})
// 结果: [3, 2, 1]

// 分块
chunks := candy.Chunk([]int{1, 2, 3, 4, 5}, 2)
// 结果: [[1, 2], [3, 4], [5]]

// 排序
sorted := candy.Sort([]int{3, 1, 4, 1, 5, 9, 2, 6})
// 结果: [1, 1, 2, 3, 4, 5, 6, 9]
```

---

## 3. 集合操作

### 3.1 查找与比较

```go
// 检查元素是否存在
users := []User{{ID: 1}, {ID: 2}, {ID: 3}}

hasUser := candy.ContainsUsing(users, func(u User) bool {
    return u.ID == 2
}) // true

// 查找元素索引
ids := []int{10, 20, 30, 40}
idx := candy.Index(ids, 30) // 2

// 切片差异
old := []int{1, 2, 3}
new := []int{2, 3, 4}

added, removed := candy.Diff(old, new)
// added = [4], removed = [1]
```

### 3.2 集合运算

```go
// 交集
common := candy.Same([]int{1, 2, 3}, []int{2, 3, 4})
// 结果: [2, 3]

// 差集
diff := candy.Spare([]int{1, 2}, []int{2, 3, 4})
// 结果: [3, 4] (在第二个但不在第一个)

// 移除元素
result := candy.Remove([]int{1, 2, 3, 4, 5}, []int{2, 4})
// 结果: [1, 3, 5]
```

---

## 4. 结构体操作

### 4.1 Pluck - 字段提取

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

type Order struct {
    ID     int
    UserID int
    Amount float64
    Status string
}

func main() {
    orders := []Order{
        {ID: 1, UserID: 10, Amount: 100.0, Status: "pending"},
        {ID: 2, UserID: 20, Amount: 200.0, Status: "completed"},
        {ID: 3, UserID: 10, Amount: 150.0, Status: "pending"},
    }

    // 提取所有订单 ID
    ids := candy.Pluck(orders, func(o Order) int {
        return o.ID
    })
    // 结果: [1, 2, 3]

    // 提取去重的用户 ID
    userIDs := candy.PluckUnique(orders, func(o Order) int {
        return o.UserID
    })
    // 结果: [10, 20]

    // 提取所有金额并求和
    amounts := candy.Pluck(orders, func(o Order) float64 {
        return o.Amount
    })
    total := candy.Sum(amounts...)
    // 结果: 450.0

    // 按状态分组
    groupedByStatus := candy.PluckGroupBy(orders, func(o Order) string {
        return o.Status
    })
    // 结果: map[string][]Order{
    //     "pending":   [{ID: 1...}, {ID: 3...}],
    //     "completed": [{ID: 2...}],
    // }

    // 构建用户 ID 到订单的映射
    userOrders := candy.PluckMap(orders,
        func(o Order) int { return o.UserID },
        func(o Order) Order { return o },
    )
    // 结果: map[int]Order{10: {ID: 3...}, 20: {ID: 2...}}

    fmt.Printf("User Orders: %v\n", userOrders)
}
```

### 4.2 KeyBy - 创建索引

```go
// 按 ID 创建快速查找索引
userIndex := candy.KeyByInt(users, "ID")
// map[int]User{1: {ID: 1, ...}, 2: {ID: 2, ...}}

// 快速查找
user := userIndex[1]

// 按 Email 创建索引（反射版本）
emailIndex := candy.KeyByString(users, "Email")
// map[string]User{"alice@example.com": {...}, ...}
```

### 4.3 SliceField2Map - 集合创建

```go
// 创建 ID 集合
idSet := candy.SliceField2MapInt(users, "ID")
// map[int]bool{1: true, 2: true, 3: true}

// 快速检查存在
exists := idSet[1] // true

// 创建邮箱集合
emailSet := candy.SliceField2MapString(users, "Email")
// map[string]bool{"alice@example.com": true, ...}
```

---

## 5. 反射与深度操作

### 5.1 深度复制

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

type Nested struct {
    Data  []int
    Info  map[string]string
}

func main() {
    original := Nested{
        Data: []int{1, 2, 3},
        Info: map[string]string{"key": "value"},
    }

    // 方法 1: Clone
    cloned := candy.Clone(original)

    // 方法 2: DeepCopy（需要预先分配）
    var copy Nested
    candy.DeepCopy(&original, &copy)

    // 修改克隆不影响原对象
    cloned.Data[0] = 999
    fmt.Printf("Original: %v, Cloned: %v\n", original.Data, cloned.Data)
    // 输出: Original: [1 2 3], Cloned: [999 2 3]

    // 切片克隆
    sliceClone := candy.CloneSlice([]Nested{original})

    // Map 克隆
    mapClone := candy.CloneMap(map[string]Nested{"a": original})
}
```

### 5.2 深度比较

```go
a := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v"}}
b := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v"}}
c := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v2"}}

equal := candy.DeepEqual(a, b) // true
equal = candy.DeepEqual(a, c)  // false

// 切片比较（不考虑顺序）
equal = candy.SliceEqual([]int{1, 2}, []int{2, 1}) // true

// Map 比较
equal = candy.MapEqual(
    map[string]int{"a": 1},
    map[string]int{"a": 1},
) // true
```

---

## 6. 实际应用场景

### 6.1 API 响应处理

```go
// 从 API 获取数据并处理
func processAPIResponse(data map[string]interface{}) []User {
    // 提取用户列表
    rawUsers, ok := data["users"].([]interface{})
    if !ok {
        return nil
    }

    // 转换为结构体
    users := make([]User, 0, len(rawUsers))
    for _, item := range rawUsers {
        userMap, ok := item.(map[string]interface{})
        if !ok {
            continue
        }

        users = append(users, User{
            ID:    candy.ToInt(userMap["id"]),
            Name:  candy.ToString(userMap["name"]),
            Age:   candy.ToInt(userMap["age"]),
            Email: candy.ToString(userMap["email"]),
        })
    }

    return users
}
```

### 6.2 数据验证

```go
// 验证必需字段是否存在
func validateUser(user User, requiredFields []string) bool {
    userMap := candy.ToMapStringAny(user)

    for _, field := range requiredFields {
        val, exists := userMap[field]
        if !exists {
            return false
        }

        // 检查非空
        if str, ok := val.(string); ok {
            if str == "" {
                return false
            }
        }
    }

    return true
}
```

### 6.3 批量操作

```go
// 批量更新用户状态
func batchUpdateStatus(users []User, status string) []User {
    updated := candy.Map(users, func(u User) User {
        u.Status = status
        return u
    })

    return updated
}

// 批量删除
func batchDelete(all []User, toDeleteIDs []int) []User {
    idSet := candy.Slice2Map(toDeleteIDs)

    return candy.Filter(all, func(u User) bool {
        return !idSet[u.ID]
    })
}
```

### 6.4 数据分组与统计

```go
// 按年龄分组统计
func groupByAge(users []User) map[string]int {
    ageGroups := map[string]string{
        "young":   "0-18",
        "adult":   "19-60",
        "senior":  "60+",
    }

    grouped := make(map[string]int)

    for _, user := range users {
        var group string
        switch {
        case user.Age <= 18:
            group = "young"
        case user.Age <= 60:
            group = "adult"
        default:
            group = "senior"
        }

        grouped[ageGroups[group]]++
    }

    return grouped
}

// 使用 PluckGroupBy 简化
func groupByAgePluck(users []User) map[string]int {
    grouped := candy.PluckGroupBy(users, func(u User) string {
        switch {
        case u.Age <= 18:
            return "young"
        case u.Age <= 60:
            return "adult"
        default:
            return "senior"
        }
    })

    // 统计每组数量
    result := make(map[string]int)
    for group, groupUsers := range grouped {
        result[group] = len(groupUsers)
    }

    return result
}
```

### 6.5 分页处理

```go
// 分页切片
func paginate[T any](items []T, page, pageSize int) []T {
    if page < 1 {
        page = 1
    }

    start := (page - 1) * pageSize
    if start >= len(items) {
        return []T{}
    }

    end := start + pageSize
    if end > len(items) {
        end = len(items)
    }

    return items[start:end]
}

// 使用示例
allUsers := getUsers() // 假设返回 100 个用户
page1 := paginate(allUsers, 1, 10)
page2 := paginate(allUsers, 2, 10)
```

---

## 性能提示

1. **预分配容量**: 对已知大小的切片，使用 `make` 预分配
2. **使用泛型**: 优先使用泛型函数而非反射版本
3. **避免不必要转换**: 直接比较而不是先转字符串
4. **批量操作**: 使用 `Filter`、`Map` 等而非手动循环

```go
// ❌ 不推荐
result := []int{}
for _, item := range items {
    result = append(result, process(item))
}

// ✅ 推荐
result := make([]int, 0, len(items))
for _, item := range items {
    result = append(result, process(item))
}

// ✅ 更推荐（使用 candy）
result := candy.Map(items, process)
```

---

## 完整示例：用户管理系统

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

type User struct {
    ID     int
    Name   string
    Age    int
    Email  string
    Active bool
}

func main() {
    // 初始化数据
    users := []User{
        {ID: 1, Name: "Alice", Age: 25, Email: "alice@example.com", Active: true},
        {ID: 2, Name: "Bob", Age: 17, Email: "bob@example.com", Active: true},
        {ID: 3, Name: "Charlie", Age: 30, Email: "charlie@example.com", Active: false},
        {ID: 4, Name: "Diana", Age: 28, Email: "diana@example.com", Active: true},
    }

    // 1. 筛选活跃成年用户
    activeAdults := candy.Filter(users, func(u User) bool {
        return u.Active && u.Age >= 18
    })

    // 2. 提取邮箱列表
    emails := candy.Map(activeAdults, func(u User) string {
        return u.Email
    })

    // 3. 创建 ID 索引
    userIndex := candy.KeyByInt(users, "ID")

    // 4. 按年龄分组
    ageGroups := candy.PluckGroupBy(users, func(u User) string {
        if u.Age < 20 {
            return "young"
        } else if u.Age < 30 {
            return "middle"
        }
        return "senior"
    })

    // 5. 统计各年龄组人数
    stats := make(map[string]int)
    for group, groupUsers := range ageGroups {
        stats[group] = len(groupUsers)
    }

    // 输出结果
    fmt.Printf("Active Adults: %v\n", emails)
    fmt.Printf("User #1: %v\n", userIndex[1])
    fmt.Printf("Age Groups: %v\n", stats)
}
```

---

## 总结

candy 模块提供了一套简洁、高效、类型安全的工具函数，特别适合：

- **数据处理管道**: Filter → Map → Reduce
- **集合操作**: 去重、排序、分组
- **类型转换**: 安全、简洁的类型转换
- **结构体操作**: 字段提取、索引创建
- **反射操作**: 深度复制、比较

通过组合这些函数，可以编写出简洁、易读、高性能的 Go 代码。
