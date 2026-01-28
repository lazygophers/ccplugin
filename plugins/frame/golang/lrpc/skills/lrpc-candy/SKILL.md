---
name: lrpc-candy
description: lazygophers/utils candy 模块完整指南 - 类型安全转换、泛型工具函数、集合操作、反射封装的最佳实践
---

# lazygophers/utils candy 模块完整指南

## 概述

`candy` 模块是 lazygophers/utils 的核心工具库，提供了一套完整的 Go 语法糖函数，专注于简化常见的编程操作。该模块具有以下特点：

- **零分配转换**：关键函数经过优化，实现零内存分配
- **类型安全**：全面使用 Go 1.18+ 泛型，提供编译时类型检查
- **高性能**：通过基准测试验证，性能比标准库快 2-3x
- **易用性**：简洁直观的 API，减少样板代码

### 性能对比

| 操作 | candy | 标准库 | 提升 |
|------|-------|--------|------|
| `ToInt()` | 12.3 ns/op | 39.5 ns/op | 3.2x |
| `ToString()` | 8.5 ns/op | 25.2 ns/op | 2.9x |

---

## 1. 类型转换函数

### 1.1 整数转换

candy 提供了完整的整数类型转换函数，支持所有整数类型之间的转换。

#### ToInt 系列函数

```go
// ToInt 将任意类型转换为 int
func ToInt(val interface{}) int

// ToInt8 将任意类型转换为 int8
func ToInt8(val interface{}) int8

// ToInt16 将任意类型转换为 int16
func ToInt16(val interface{}) int16

// ToInt32 将任意类型转换为 int32
func ToInt32(val interface{}) int32

// ToInt64 将任意类型转换为 int64
func ToInt64(val interface{}) int64
```

**支持的输入类型：**
- `bool`: true → 1, false → 0
- 所有整数类型 (int, int8, int16, int32, int64)
- 所有无符号整数 (uint, uint8, uint16, uint32, uint64)
- 浮点数 (float32, float64): 直接截断小数部分
- `string`, `[]byte`: 解析十进制字符串，失败返回 0
- `time.Duration` (仅 ToInt64)

**使用示例：**

```go
// 基础类型转换
n := candy.ToInt(42.7)        // 42
n := candy.ToInt("123")       // 123
n := candy.ToInt(true)        // 1
n := candy.ToInt(false)       // 0
n := candy.ToInt([]byte("456")) // 456

// 错误处理
n := candy.ToInt("invalid")  // 0
n := candy.ToInt(nil)        // 0

// int64 特殊支持
duration := candy.ToInt64(time.Second)  // 1000000000
```

#### ToUint 系列函数

```go
// ToUint 将任意类型转换为 uint
func ToUint(val interface{}) uint

// ToUint8 将任意类型转换为 uint8
func ToUint8(val interface{}) uint8

// ToUint16 将任意类型转换为 uint16
func ToUint16(val interface{}) uint16

// ToUint32 将任意类型转换为 uint32
func ToUint32(val interface{}) uint32

// ToUint64 将任意类型转换为 uint64
func ToUint64(val interface{}) uint64
```

**重要特性：**
- 负数转换结果为 0（而非下溢）
- 其他类型支持与 ToInt 系列相同

**使用示例：**

```go
u := candy.ToUint(42)           // 42
u := candy.ToUint(-10)          // 0 (负数处理)
u := candy.ToUint("100")        // 100
u := candy.ToUint(true)         // 1
```

### 1.2 浮点数转换

```go
// ToFloat32 将任意类型转换为 float32
func ToFloat32(val interface{}) float32

// ToFloat64 将任意类型转换为 float64
func ToFloat64(val interface{}) float64
```

**支持的输入类型：**
- `bool`: true → 1.0, false → 0.0
- 所有整数类型
- 浮点数
- `string`, `[]byte`: 先尝试解析为浮点数，失败则尝试解析为整数

**使用示例：**

```go
f := candy.ToFloat64(42)        // 42.0
f := candy.ToFloat64("3.14")    // 3.14
f := candy.ToFloat64("123")     // 123.0 (自动回退到整数解析)
f := candy.ToFloat64(true)      // 1.0
```

### 1.3 布尔值转换

```go
// ToBool 将任意类型转换为 bool
func ToBool(val interface{}) bool
```

**转换规则：**

| 类型 | 转换为 true | 转换为 false |
|------|-------------|--------------|
| `bool` | true | false |
| 整数 | 非 0 | 0 |
| 浮点数 | 非 0.0 且非 NaN | 0.0 或 NaN |
| `string`/`[]byte` | "true", "1", "t", "y", "yes", "on" | "false", "0", "f", "n", "no", "off", "" |
| `nil` | - | false |
| 其他类型 | - | false |

**使用示例：**

```go
b := candy.ToBool(true)         // true
b := candy.ToBool(1)            // true
b := candy.ToBool(0)            // false
b := candy.ToBool("yes")        // true
b := candy.ToBool("no")         // false
b := candy.ToBool("hello")      // true (非空字符串)
b := candy.ToBool("")           // false
b := candy.ToBool(nil)          // false
b := candy.ToBool(3.14)         // true
b := candy.ToBool(0.0)          // false
b := candy.ToBool(math.NaN())   // false
```

### 1.4 字符串转换

```go
// ToString 将任意类型转换为 string
func ToString(val interface{}) string
```

**转换规则：**

| 类型 | 转换结果 |
|------|----------|
| `bool` | "1" / "0" |
| 整数 | 十进制字符串 |
| 浮点数 | 整数返回无小数点，否则保留精度 |
| `time.Duration` | Duration.String() 格式 |
| `string` | 原值 |
| `[]byte` | 转换为 string |
| `nil` | "" |
| `error` | Error() 信息 |
| 其他类型 | JSON 序列化 |

**使用示例：**

```go
s := candy.ToString(42)         // "42"
s := candy.ToString(3.14)       // "3.14"
s := candy.ToString(3.0)        // "3"
s := candy.ToString(true)       // "1"
s := candy.ToString([]byte{65, 66}) // "AB"
s := candy.ToString(time.Hour)  // "1h0m0s"
s := candy.ToString(nil)        // ""
s := candy.ToString(errors.New("error")) // "error"

// 复杂类型 JSON 序列化
type User struct { ID int; Name string }
s := candy.ToString(User{ID: 1, Name: "Alice"}) // {"ID":1,"Name":"Alice"}
```

### 1.5 字节切片转换

```go
// ToBytes 将任意类型转换为 []byte
func ToBytes(val interface{}) []byte
```

**支持的类型：** 与 ToString 类似，但返回字节切片。

**使用示例：**

```go
b := candy.ToBytes("hello")     // []byte{104, 101, 108, 108, 111}
b := candy.ToBytes(42)          // []byte("42")
b := candy.ToBytes(true)        // []byte("1")
b := candy.ToBytes(nil)         // nil
```

### 1.6 切片类型转换

```go
// ToInt64Slice 将切片转换为 []int64
func ToInt64Slice(val interface{}) []int64

// ToFloat64Slice 将切片转换为 []float64
func ToFloat64Slice(val interface{}) []float64

// ToStringSlice 将任意类型转换为 []string
func ToStringSlice(v interface{}) []string
```

**使用示例：**

```go
// 切片转换
nums := candy.ToInt64Slice([]int{1, 2, 3})    // []int64{1, 2, 3}
nums := candy.ToInt64Slice([]string{"1", "2"}) // []int64{1, 2}

floats := candy.ToFloat64Slice([]int{1, 2, 3}) // []float64{1.0, 2.0, 3.0}

// 字符串切片特殊处理
strs := candy.ToStringSlice("a,b,c")  // []string{"a", "b", "c"}
strs := candy.ToStringSlice("hello")  // []string{"hello"}
strs := candy.ToStringSlice([]int{1, 2, 3}) // []string{"1", "2", "3"}
```

### 1.7 Map 类型转换

```go
// ToMap 将任意类型转换为 map[string]interface{}
func ToMap(v interface{}) map[string]interface{}

// ToMapStringString 将任意类型转换为 map[string]string
func ToMapStringString(v interface{}) map[string]string

// ToMapStringInt64 将任意类型转换为 map[string]int64
func ToMapStringInt64(v interface{}) map[string]int64

// ToMapStringAny 将任意类型转换为 map[string]interface{}
func ToMapStringAny(v interface{}) map[string]interface{}
```

**使用示例：**

```go
// 从 JSON 字符串转换
m := candy.ToMap([]byte(`{"a":1,"b":"hello"}`))
// 结果: map[string]interface{}{"a":1, "b":"hello"}

// 类型化 map 转换
m := candy.ToMapStringString(map[interface{}]interface{}{1: "a", "b": "c"})
// 结果: map[string]string{"1": "a", "b": "c"}

m := candy.ToMapStringInt64(map[string]interface{}{"a": "123", "b": 456})
// 结果: map[string]int64{"a": 123, "b": 456}
```

### 1.8 指针转换

```go
// ToPtr 将值转换为指针
func ToPtr[T any](v T) *T
```

**使用示例：**

```go
// 创建指针的简洁方式
p := candy.ToPtr(42)        // *int 指向 42
p := candy.ToPtr("hello")   // *string 指向 "hello"

// 可选参数默认值
func foo(name *string) {
    n := candy.ToPtr("default")
    if name != nil {
        n = name
    }
    fmt.Println(*n)
}
```

---

## 2. 泛型工具函数

### 2.1 数学运算

```go
// Max 返回最大值
func Max[T constraints.Ordered](ss ...T) T

// Min 返回最小值
func Min[T constraints.Ordered](ss ...T) T

// Sum 计算总和
func Sum[T constraints.Ordered](ss ...T) T

// Average 计算平均值
func Average[T constraints.Integer | constraints.Float | time.Duration](ss ...T) T

// Abs 计算绝对值
func Abs[T constraints.Integer | constraints.Float](s T) T
```

**使用示例：**

```go
// Max/Min - 支持可变参数
max := candy.Max(1, 5, 3, 9, 2)  // 9
min := candy.Min(1, 5, 3, 9, 2)  // 1

// 切片展开
nums := []int{1, 5, 3, 9, 2}
max := candy.Max(nums...)  // 9

// 不同类型
max := candy.Max("apple", "banana", "cherry")  // "cherry" (字典序)
max := candy.Max(3.14, 2.71, 1.41)  // 3.14

// Sum
sum := candy.Sum(1, 2, 3, 4, 5)  // 15
sum := candy.Sum(1.5, 2.5, 3.0)  // 7.0

// Average
avg := candy.Average(1, 2, 3, 4, 5)  // 3
avg := candy.Average(1.0, 2.0, 3.0)  // 2.0

// Abs
abs := candy.Abs(-42)   // 42
abs := candy.Abs(3.14)  // 3.14
```

### 2.2 切片操作

#### 访问元素

```go
// First 返回第一个元素，空切片返回零值
func First[T any](ss []T) T

// FirstOr 返回第一个元素，空切片返回默认值
func FirstOr[T any](ss []T, or T) T

// Last 返回最后一个元素，空切片返回零值
func Last[T any](ss []T) T

// LastOr 返回最后一个元素，空切片返回默认值
func LastOr[T any](ss []T, or T) T

// Top 返回前 n 个元素
func Top[T any](ss []T, n int) []T

// Bottom 返回最后 n 个元素
func Bottom[T any](ss []T, n int) []T
```

**使用示例：**

```go
nums := []int{1, 2, 3, 4, 5}

// First/Last
first := candy.First(nums)      // 1
first := candy.First([]int{})   // 0 (零值)

first := candy.FirstOr(nums, 99)       // 1
first := candy.FirstOr([]int{}, 99)    // 99

last := candy.Last(nums)        // 5
last := candy.LastOr(nums, 99)  // 5

// Top/Bottom
top3 := candy.Top(nums, 3)      // [1, 2, 3]
top10 := candy.Top(nums, 10)    // [1, 2, 3, 4, 5] (不超过切片长度)

bottom3 := candy.Bottom(nums, 3) // [3, 4, 5]
```

#### 切片过滤与转换

```go
// Filter 过滤切片
func Filter[T any](ss []T, f func(T) bool) []T

// FilterNot 反向过滤
func FilterNot[T any](ss []T, f func(T) bool) []T

// Map 映射切片
func Map[T, U any](ss []T, f func(T) U) []U

// Reduce 归约切片
func Reduce[T any](ss []T, f func(T, T) T) T
```

**使用示例：**

```go
nums := []int{1, 2, 3, 4, 5, 6}

// Filter - 保留偶数
evens := candy.Filter(nums, func(n int) bool {
    return n%2 == 0
})  // [2, 4, 6]

// FilterNot - 移除偶数
odds := candy.FilterNot(nums, func(n int) bool {
    return n%2 == 0
})  // [1, 3, 5]

// Map - 转换类型
doubled := candy.Map(nums, func(n int) int {
    return n * 2
})  // [2, 4, 6, 8, 10, 12]

// Map - 类型转换
strs := candy.Map(nums, func(n int) string {
    return candy.ToString(n)
})  // ["1", "2", "3", "4", "5", "6"]

// Reduce - 求和
sum := candy.Reduce(nums, func(a, b int) int {
    return a + b
})  // 21
```

#### 切片重组

```go
// Unique 去重，保持顺序
func Unique[T constraints.Ordered](ss []T) []T

// UniqueUsing 使用函数去重
func UniqueUsing[T any](ss []T, f func(T) any) []T

// Reverse 反转切片
func Reverse[T any](ss []T) []T

// Shuffle 随机打乱切片
func Shuffle[T any](ss []T) []T

// Sort 排序切片
func Sort[T constraints.Ordered](ss []T) []T

// SortUsing 自定义排序
func SortUsing[T any](slice []T, less func(T, T) bool) []T

// Chunk 分块切片
func Chunk[T any](ss []T, size int) [][]T

// Drop 丢弃前 n 个元素
func Drop[T any](ss []T, n int) []T

// Join 连接切片为字符串
func Join[T constraints.Ordered](ss []T, glue ...string) string
```

**使用示例：**

```go
// Unique - 简单类型去重
nums := []int{1, 2, 2, 3, 4, 4, 5}
unique := candy.Unique(nums)  // [1, 2, 3, 4, 5]

// UniqueUsing - 复杂类型去重
type User struct { ID int; Name string }
users := []User{{1, "Alice"}, {2, "Bob"}, {1, "Alice2"}}
unique := candy.UniqueUsing(users, func(u User) any {
    return u.ID
})  // [{1 Alice}, {2 Bob}]

// Reverse
reversed := candy.Reverse([]int{1, 2, 3})  // [3, 2, 1]

// Shuffle - Fisher-Yates 洗牌算法
cards := []int{1, 2, 3, 4, 5}
shuffled := candy.Shuffle(cards)

// Sort
sorted := candy.Sort([]int{3, 1, 4, 1, 5})  // [1, 1, 3, 4, 5]

// SortUsing - 自定义比较
users := []User{{3, "Charlie"}, {1, "Alice"}, {2, "Bob"}}
sorted := candy.SortUsing(users, func(a, b User) bool {
    return a.Name < b.Name
})  // 按 Name 排序

// Chunk
chunks := candy.Chunk([]int{1, 2, 3, 4, 5}, 2)  // [[1, 2], [3, 4], [5]]

// Drop
dropped := candy.Drop([]int{1, 2, 3, 4, 5}, 2)  // [3, 4, 5]

// Join
joined := candy.Join([]int{1, 2, 3}, "-")  // "1-2-3"
joined := candy.Join([]string{"a", "b", "c"}, ",")  // "a,b,c"
```

#### 切片查找与比较

```go
// Contains 检查是否包含元素
func Contains[T constraints.Ordered](ss []T, s T) bool

// ContainsUsing 使用函数检查
func ContainsUsing[T any](ss []T, f func(v T) bool) bool

// Index 查找元素索引
func Index[T constraints.Ordered](ss []T, sub T) int

// SliceEqual 切片相等性检查
func SliceEqual[T any](a, b []T) bool
```

**使用示例：**

```go
nums := []int{1, 2, 3, 4, 5}

// Contains
has := candy.Contains(nums, 3)   // true
has := candy.Contains(nums, 10)  // false

// ContainsUsing - 自定义条件
has := candy.ContainsUsing(nums, func(n int) bool {
    return n > 3
})  // true (存在大于 3 的元素)

// Index
idx := candy.Index(nums, 3)   // 2
idx := candy.Index(nums, 10)  // -1

// SliceEqual - 不考虑顺序
equal := candy.SliceEqual([]int{1, 2, 3}, []int{3, 2, 1})  // true
equal := candy.SliceEqual([]int{1, 2}, []int{1, 2, 3})     // false
```

#### 切片差异与集合操作

```go
// Diff 计算差异
func Diff[T constraints.Ordered](ss, against []T) (added, removed []T)

// Same 返回交集
func Same[T constraints.Ordered](against, ss []T) []T

// Spare 返回差集 (against - ss)
func Spare[T constraints.Ordered](ss, against []T) []T

// Remove 移除元素
func Remove[T constraints.Ordered](ss, toRemove []T) []T

// RemoveIndex 移除指定索引
func RemoveIndex[T any](ss []T, index int) []T
```

**使用示例：**

```go
old := []int{1, 2, 3}
new := []int{2, 3, 4}

// Diff - 查找新增和删除
added, removed := candy.Diff(old, new)
// added = [4], removed = [1]

// Same - 交集
common := candy.Same(old, new)  // [2, 3]

// Spare - 差集
diff := candy.Spare(old, new)   // [4]

// Remove - 批量移除
result := candy.Remove([]int{1, 2, 3, 4, 5}, []int{2, 4})  // [1, 3, 5]

// RemoveIndex - 移除单个元素
result := candy.RemoveIndex([]int{1, 2, 3, 4}, 2)  // [1, 2, 4]
```

#### 遍历与判断

```go
// All 检查所有元素是否满足条件
func All[T any](ss []T, f func(T) bool) bool

// Any 检查是否存在元素满足条件
func Any[T any](ss []T, f func(T) bool) bool

// Each 遍历切片
func Each[T any](values []T, fn func(value T))

// EachReverse 反向遍历切片
func EachReverse[T any](ss []T, f func(T))
```

**使用示例：**

```go
nums := []int{2, 4, 6, 8, 10}

// All - 所有元素都是偶数
allEven := candy.All(nums, func(n int) bool {
    return n%2 == 0
})  // true

// Any - 存在大于 5 的元素
anyBig := candy.Any(nums, func(n int) bool {
    return n > 5
})  // true

// Each - 遍历执行
candy.Each(nums, func(n int) {
    fmt.Println(n)
})

// EachReverse - 反向遍历
candy.EachReverse(nums, func(n int) {
    fmt.Println(n)
})  // 10, 8, 6, 4, 2
```

### 2.3 Map 操作

```go
// MapKeys 获取 map 的所有 key
func MapKeys[K constraints.Ordered, V any](m map[K]V) []K

// MapValues 获取 map 的所有 value
func MapValues[K constraints.Ordered, V any](m map[K]V) []V

// 反射版本 - 支持任意类型
func MapKeysInt(m interface{}) []int
func MapKeysString(m interface{}) []string
func MapKeysAny(m interface{}) []interface{}
// ... 其他类型类似
```

**使用示例：**

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}

// MapKeys - 泛型版本
keys := candy.MapKeys(m)  // []string{"a", "b", "c"} (顺序不确定)

// MapValues
values := candy.MapValues(m)  // []int{1, 2, 3}

// 反射版本 - 用于 interface{}
var anyMap interface{} = map[int]string{1: "a", 2: "b"}
keys := candy.MapKeysInt(anyMap)  // []int{1, 2}
```

### 2.4 Pluck - 结构体字段提取

```go
// 泛型版本 - 推荐
func Pluck[T any, U any](slice []T, selector func(T) U) []U

func PluckPtr[T any, U any](slice []*T, selector func(*T) U, defaultVal U) []U

func PluckUnique[T any, U comparable](slice []T, selector func(T) U) []U

func PluckMap[T any, K comparable, V any](slice []T, keySelector func(T) K, valueSelector func(T) V) map[K]V

func PluckGroupBy[T any, K comparable](slice []T, keySelector func(T) K) map[K][]T

// 反射版本 - 向后兼容
func PluckInt(list interface{}, fieldName string) []int
func PluckString(list interface{}, fieldName string) []string
func PluckInt64(list interface{}, fieldName string) []int64
// ... 其他类型
```

**使用示例：**

```go
type User struct {
    ID   int
    Name string
    Age  int
}

users := []User{
    {ID: 1, Name: "Alice", Age: 25},
    {ID: 2, Name: "Bob", Age: 30},
    {ID: 3, Name: "Charlie", Age: 25},
}

// Pluck - 提取单个字段
names := candy.Pluck(users, func(u User) string {
    return u.Name
})  // ["Alice", "Bob", "Charlie"]

ages := candy.Pluck(users, func(u User) int {
    return u.Age
})  // [25, 30, 25]

// PluckPtr - 处理指针切片
userPtrs := []*User{{ID: 1, Name: "Alice"}, nil, {ID: 2, Name: "Bob"}}
names := candy.PluckPtr(userPtrs, func(u *User) string {
    return u.Name
}, "unknown")  // ["Alice", "unknown", "Bob"]

// PluckUnique - 去重提取
uniqueAges := candy.PluckUnique(users, func(u User) int {
    return u.Age
})  // [25, 30]

// PluckMap - 构建 map
idToName := candy.PluckMap(users,
    func(u User) int { return u.ID },
    func(u User) string { return u.Name },
)  // map[int]string{1: "Alice", 2: "Bob", 3: "Charlie"}

// PluckGroupBy - 分组
ageToUsers := candy.PluckGroupBy(users, func(u User) int {
    return u.Age
})  // map[int][]User{25: [{1 Alice 25}, {3 Charlie 25}], 30: [{2 Bob 30}]}

// 反射版本 - 字符串字段名
names := candy.PluckString(users, "Name")  // ["Alice", "Bob", "Charlie"]
ids := candy.PluckInt(users, "ID")         // [1, 2, 3]
```

### 2.5 KeyBy - 结构体切片转 Map

```go
// KeyByInt 将结构体切片按 int 字段转为 map
func KeyByInt[T any](ss []T, fieldName string) map[int]T

// KeyByString 将结构体切片按 string 字段转为 map
func KeyByString[T any](ss []T, fieldName string) map[string]T

// KeyByInt64, KeyByInt32, KeyByUint, KeyByUint64 等
// KeyByFloat32, KeyByFloat64
// KeyByBool
```

**使用示例：**

```go
type User struct {
    ID   int
    Name string
}

users := []User{
    {ID: 1, Name: "Alice"},
    {ID: 2, Name: "Bob"},
}

// KeyByInt - 按 ID 转为 map
userMap := candy.KeyByInt(users, "ID")
// map[int]User{1: {ID: 1, Name: "Alice"}, 2: {ID: 2, Name: "Bob"}}

// KeyByString - 按 Name 转为 map
nameMap := candy.KeyByString(users, "Name")
// map[string]User{"Alice": {ID: 1, Name: "Alice"}, ...}

// 访问
user := userMap[1]  // {ID: 1, Name: "Alice"}
```

### 2.6 SliceField2Map - 字段值提取为 Set

```go
// SliceField2MapInt 提取 int 字段值作为 map key
func SliceField2MapInt[T any](ss []T, fieldName string) map[int]bool

// SliceField2MapString 提取 string 字段值作为 map key
func SliceField2MapString[T any](ss []T, fieldName string) map[string]bool

// SliceField2MapInt64, SliceField2MapInt8, SliceField2MapUint 等
// SliceField2MapFloat32, SliceField2MapFloat64
// SliceField2MapBool
```

**使用示例：**

```go
type User struct {
    ID   int
    Name string
    Age  int
}

users := []User{
    {ID: 1, Name: "Alice", Age: 25},
    {ID: 2, Name: "Bob", Age: 30},
    {ID: 3, Name: "Charlie", Age: 25},
}

// SliceField2MapInt - 提取 ID 集合
idSet := candy.SliceField2MapInt(users, "ID")
// map[int]bool{1: true, 2: true, 3: true}

// 检查是否存在
exists := idSet[1]  // true
exists := idSet[10] // false

// SliceField2MapString - 提取 Name 集合
nameSet := candy.SliceField2MapString(users, "Name")
// map[string]bool{"Alice": true, "Bob": true, "Charlie": true}

// SliceField2MapInt - 提取 Age 集合 (自动去重)
ageSet := candy.SliceField2MapInt(users, "Age")
// map[int]bool{25: true, 30: true}
```

### 2.7 Slice2Map - 切片转布尔 Map

```go
// Slice2Map 将切片转为 map[T]bool
func Slice2Map[M constraints.Ordered](list []M) map[M]bool
```

**使用示例：**

```go
// 简单切片转 set
nums := []int{1, 2, 3, 4, 5}
numSet := candy.Slice2Map(nums)
// map[int]bool{1: true, 2: true, 3: true, 4: true, 5: true}

// 快速查找
exists := numSet[3]  // true
exists := numSet[10] // false

// 字符串集合
strs := []string{"apple", "banana", "cherry"}
strSet := candy.Slice2Map(strs)
// map[string]bool{"apple": true, "banana": true, "cherry": true}
```

---

## 3. 反射与深度操作

### 3.1 深度复制

```go
// DeepCopy 深度复制对象
func DeepCopy(src, dst any)

// Clone 克隆对象
func Clone[T any](src T) T

// CloneSlice 克隆切片
func CloneSlice[T any](src []T) []T

// CloneMap 克隆 map
func CloneMap[K comparable, V any](src map[K]V) map[K]V

// TypedSliceCopy 类型安全的切片复制
func TypedSliceCopy[T any](src []T) []T

// TypedMapCopy 类型安全的 map 复制
func TypedMapCopy[K comparable, V any](src map[K]V) map[K]V
```

**使用示例：**

```go
// DeepCopy - 需要预先分配目标
type Nested struct {
    Data []int
    Info map[string]string
}

src := Nested{
    Data: []int{1, 2, 3},
    Info: map[string]string{"key": "value"},
}

var dst Nested
candy.DeepCopy(&src, &dst)

// 修改 dst 不影响 src
dst.Data[0] = 999
fmt.Println(src.Data[0])  // 1 (未改变)

// Clone - 自动创建副本
cloned := candy.Clone(src)
cloned.Data[0] = 999
fmt.Println(src.Data[0])  // 1 (未改变)

// CloneSlice
slice := []Nested{src}
clonedSlice := candy.CloneSlice(slice)

// CloneMap
m := map[string]Nested{"a": src}
clonedMap := candy.CloneMap(m)

// TypedSliceCopy - 基本类型快速复制
nums := []int{1, 2, 3}
copied := candy.TypedSliceCopy(nums)  // 使用 copy() 优化

// TypedMapCopy - 基本类型快速复制
m := map[string]int{"a": 1, "b": 2}
copied := candy.TypedMapCopy(m)  // 直接赋值
```

### 3.2 深度相等性判断

```go
// DeepEqual 深度比较
func DeepEqual[M any](x, y M) bool

// Equal 通用相等性检查
func Equal[T comparable](a, b T) bool

// EqualSlice 切片相等性检查
func EqualSlice[T comparable](a, b []T) bool

// EqualMap map 相等性检查
func EqualMap[K, V comparable](a, b map[K]V) bool

// GenericSliceEqual 类型安全的切片比较
func GenericSliceEqual[T comparable](a, b []T) bool

// MapEqual 类型安全的 map 比较
func MapEqual[K, V comparable](a, b map[K]V) bool
```

**使用示例：**

```go
// DeepEqual - 递归比较
type Nested struct {
    Data []int
    Info map[string]string
}

a := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v"}}
b := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v"}}
c := Nested{Data: []int{1, 2}, Info: map[string]string{"k": "v2"}}

equal := candy.DeepEqual(a, b)  // true
equal := candy.DeepEqual(a, c)  // false

// Equal - 简单类型
equal := candy.Equal(1, 1)  // true

// EqualSlice - 切片相等
equal := candy.EqualSlice([]int{1, 2}, []int{1, 2})  // true
equal := candy.EqualSlice([]int{1, 2}, []int{2, 1})  // false (顺序敏感)

// SliceEqual - 不考虑顺序
equal := candy.SliceEqual([]int{1, 2}, []int{2, 1})  // true

// EqualMap
equal := candy.EqualMap(
    map[string]int{"a": 1, "b": 2},
    map[string]int{"b": 2, "a": 1},
)  // true
```

---

## 4. 最佳实践

### 4.1 类型转换

**推荐：** 优先使用 candy 的类型转换函数，而非手动类型断言。

```go
// ❌ 不推荐
var i int
switch v := val.(type) {
case int:
    i = v
case string:
    i, _ = strconv.Atoi(v)
}

// ✅ 推荐
i := candy.ToInt(val)
```

### 4.2 泛型函数

**推荐：** 使用泛型函数替代反射版本，性能更好且类型安全。

```go
// ❌ 不推荐 - 反射版本
names := candy.PluckString(users, "Name")

// ✅ 推荐 - 泛型版本
names := candy.Pluck(users, func(u User) string {
    return u.Name
})
```

### 4.3 切片操作链

**推荐：** 组合使用 candy 函数，创建清晰的数据处理管道。

```go
// 复杂处理管道
result := candy.Filter(users, func(u User) bool {
        return u.Age >= 18
    }).
    Filter(func(u User) bool {
        return u.IsActive
    }).
    Map(func(u User) string {
        return u.Name
    }).
    Unique()

// 更清晰的分步写法
adults := candy.Filter(users, func(u User) bool {
    return u.Age >= 18
})

activeAdults := candy.Filter(adults, func(u User) bool {
    return u.IsActive
})

names := candy.Map(activeAdults, func(u User) string {
    return u.Name
})

uniqueNames := candy.Unique(names)
```

### 4.4 深度复制

**推荐：** 根据类型选择合适的复制策略。

```go
// 基本类型切片 - 使用 copy
nums := []int{1, 2, 3}
copied := candy.TypedSliceCopy(nums)

// 复杂类型 - 使用深度复制
complex := []Nested{{Data: []int{1}}}
copied := candy.CloneSlice(complex)
```

### 4.5 错误处理

**注意：** candy 的类型转换函数不会返回错误，而是返回零值。

```go
// 字符串解析失败
n := candy.ToInt("invalid")  // 返回 0，不 panic

// 如果需要错误处理，使用标准库
n, err := strconv.Atoi("invalid")
if err != nil {
    // 处理错误
}
```

---

## 5. 性能优化建议

### 5.1 预分配切片容量

```go
// ❌ 不推荐 - 多次重新分配
result := []int{}
for _, item := range items {
    result = append(result, process(item))
}

// ✅ 推荐 - 预分配
result := make([]int, 0, len(items))
for _, item := range items {
    result = append(result, process(item))
}
```

### 5.2 使用泛型而非反射

```go
// ❌ 慢 - 反射
names := candy.PluckString(users, "Name")

// ✅ 快 - 泛型
names := candy.Pluck(users, func(u User) string { return u.Name })
```

### 5.3 避免不必要的类型转换

```go
// ❌ 不必要
if candy.ToString(status) == "active" { }

// ✅ 直接比较
if status == "active" { }
```

---

## 6. 常见问题

### Q1: 为什么 ToInt("invalid") 返回 0 而不是错误？

A: candy 的设计理念是"尽力转换"，失败时返回零值而不是错误。这简化了错误处理流程。如果需要错误信息，请使用标准库的 `strconv` 包。

### Q2: 泛型版本和反射版本如何选择？

A: 优先使用泛型版本（性能更好、类型安全）。反射版本主要用于：
- 需要通过字符串字段名访问的场景
- 与旧代码兼容

### Q3: Unique 函数保证顺序吗？

A: 是的，`Unique` 和 `UniqueUsing` 都会保持原始顺序，只保留第一次出现的元素。

### Q4: Shuffle 是否线程安全？

A: 不，`Shuffle` 会原地修改切片。如果需要线程安全，先克隆切片：

```go
shuffled := candy.Shuffle(candy.CloneSlice(original))
```

### Q5: DeepCopy 会复制未导出字段吗？

A: 会，但需要字段可设置（CanSet() == true）。未导出字段在反射中通常不可设置。

---

## 7. 完整示例

### 7.1 数据处理管道

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

type User struct {
    ID      int
    Name    string
    Age     int
    Active  bool
    Country string
}

func main() {
    users := []User{
        {ID: 1, Name: "Alice", Age: 25, Active: true, Country: "USA"},
        {ID: 2, Name: "Bob", Age: 17, Active: true, Country: "UK"},
        {ID: 3, Name: "Charlie", Age: 30, Active: false, Country: "USA"},
        {ID: 4, Name: "Diana", Age: 28, Active: true, Country: "UK"},
    }

    // 1. 筛选活跃且成年的用户
    activeAdults := candy.Filter(users, func(u User) bool {
        return u.Active && u.Age >= 18
    })

    // 2. 按国家分组
    groupedByCountry := candy.PluckGroupBy(activeAdults, func(u User) string {
        return u.Country
    })

    // 3. 提取姓名
    namesByCountry := make(map[string][]string)
    for country, countryUsers := range groupedByCountry {
        names := candy.Map(countryUsers, func(u User) string {
            return u.Name
        })
        namesByCountry[country] = names
    }

    // 4. 按 ID 创建索引
    userIndex := candy.KeyByInt(users, "ID")

    fmt.Printf("Grouped: %v\n", namesByCountry)
    fmt.Printf("User #1: %v\n", userIndex[1])
}
```

### 7.2 类型安全转换

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/candy"
)

func main() {
    // 从配置读取（可能是字符串、数字等）
    config := map[string]interface{}{
        "timeout": "30",
        "retries": 3,
        "enabled": "yes",
        "rate": 1.5,
    }

    // 安全转换
    timeout := candy.ToInt(config["timeout"])     // 30
    retries := candy.ToInt(config["retries"])     // 3
    enabled := candy.ToBool(config["enabled"])    // true
    rate := candy.ToFloat64(config["rate"])       // 1.5

    fmt.Printf("Timeout: %d, Retries: %d, Enabled: %v, Rate: %.2f\n",
        timeout, retries, enabled, rate)
}
```

---

## 8. 参考资料

- **GitHub**: https://github.com/lazygophers/utils/tree/master/candy
- **Go 版本要求**: Go 1.18+ (泛型支持)
- **依赖**: `golang.org/x/exp/constraints`

## 9. API 快速索引

### 类型转换
- `ToInt`, `ToInt8`, `ToInt16`, `ToInt32`, `ToInt64`
- `ToUint`, `ToUint8`, `ToUint16`, `ToUint32`, `ToUint64`
- `ToFloat32`, `ToFloat64`
- `ToBool`, `ToString`, `ToBytes`
- `ToInt64Slice`, `ToFloat64Slice`, `ToStringSlice`
- `ToMap`, `ToMapStringString`, `ToMapStringInt64`

### 数学运算
- `Max`, `Min`, `Sum`, `Average`, `Abs`

### 切片操作
- `First`, `FirstOr`, `Last`, `LastOr`, `Top`, `Bottom`
- `Filter`, `FilterNot`, `Map`, `Reduce`
- `Unique`, `UniqueUsing`, `Reverse`, `Shuffle`, `Sort`
- `Contains`, `ContainsUsing`, `Index`
- `Diff`, `Same`, `Spare`, `Remove`, `RemoveIndex`
- `All`, `Any`, `Each`, `EachReverse`
- `Chunk`, `Drop`, `Join`

### Map 操作
- `MapKeys`, `MapValues`

### 结构体操作
- `Pluck`, `PluckPtr`, `PluckUnique`, `PluckMap`, `PluckGroupBy`
- `KeyByInt`, `KeyByString`, `KeyByInt64` 等
- `SliceField2MapInt`, `SliceField2MapString` 等

### 反射与深度操作
- `DeepCopy`, `Clone`, `CloneSlice`, `CloneMap`
- `DeepEqual`, `Equal`, `EqualSlice`, `EqualMap`

### 泛型辅助
- `ToPtr`, `Slice2Map`
