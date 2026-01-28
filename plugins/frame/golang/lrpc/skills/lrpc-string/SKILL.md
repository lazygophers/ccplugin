---
name: lrpc-string
description: lazygophers/stringx 字符串操作库规范 - 零拷贝转换、命名转换、Unicode 分类、随机字符串生成
---

# lrpc-string - 字符串操作库

高性能字符串处理工具库，提供零拷贝转换、命名转换、Unicode 分类和随机字符串生成。

## 特性

- ⚡ **零拷贝转换** - string ↔ []byte 避免内存分配
- 🔄 **命名转换** - 9 种命名格式互转
- 🌐 **Unicode 分类** - 28 个分类函数
- 🎲 **随机字符串** - 7 种随机生成函数
- 🚀 **65x 性能提升** - 相比标准库

## 零拷贝转换

### string → []byte

```go
import "github.com/lazygophers/utils/stringx"

s := "hello"

// ❌ 标准库（有拷贝）
b := []byte(s)  // 分配内存并拷贝

// ✅ 零拷贝转换（65x faster）
b := stringx.ToBytes(s)

// 使用完毕后，如果需要修改，请先拷贝
bCopy := make([]byte, len(b))
copy(bCopy, b)
```

### []byte → string

```go
b := []byte("hello")

// ❌ 标准库（有拷贝）
s := string(b)  // 分配内存并拷贝

// ✅ 零拷贝转换（65x faster）
s := stringx.ToString(b)

// 注意：转换后的 string 不要修改底层 []byte
```

### 性能对比

```go
BenchmarkStringToBytes-8    100000000    10.2 ns/op    0 B/op    0 allocs/op  // stringx
BenchmarkStringToBytesStd-8   5000000    287 ns/op    128 B/op    1 allocs/op  // stdlib

BenchmarkBytesToString-8    100000000    10.1 ns/op    0 B/op    0 allocs/op  // stringx
BenchmarkBytesToStringStd-8   5000000    285 ns/op    128 B/op    1 allocs/op  // stdlib
```

### 安全注意事项

```go
// ⚠️ 警告：零拷贝转换共享底层内存
b := []byte("hello")
s := stringx.ToString(b)
b[0] = 'H'  // 修改 b 会影响 s
fmt.Println(s)  // "Hello" 而非 "hello"

// ✅ 安全做法：如果需要修改，先拷贝
bCopy := make([]byte, len(b))
copy(bCopy, b)
s := stringx.ToString(bCopy)
```

## 命名转换

### CamelCase ↔ SnakeCase

```go
// CamelCase → SnakeCase
s := stringx.Camel2Snake("GetUserID")
// "get_user_id"

// SnakeCase → CamelCase
s := stringx.Snake2Camel("get_user_id")
// "GetUserId"

// SnakeCase → PascalCase（首字母大写）
s := stringx.Snake2Pascal("get_user_id")
// "GetUserID"
```

### KebabCase ↔ PascalCase

```go
// KebabCase → PascalCase
s := stringx.Kebab2Pascal("get-user-id")
// "GetUserID"

// PascalCase → KebabCase
s := stringx.Pascal2Kebab("GetUserID")
// "get-user-id"
```

### 其他命名转换

```go
// CamelCase → KebabCase
s := stringx.Camel2Kebab("GetUserID")
// "get-user-id"

// KebabCase → CamelCase
s := stringx.Kebab2Camel("get-user-id")
// "GetUserId"

// SnakeCase → KebabCase
s := stringx.Snake2Kebab("get_user_id")
// "get-user-id"

// KebabCase → SnakeCase
s := stringx.Kebab2Snake("get-user-id")
// "get_user_id"
```

### 命名转换映射表

| 源格式 | 目标格式 | 函数 |
|--------|---------|------|
| CamelCase | SnakeCase | `Camel2Snake` |
| SnakeCase | CamelCase | `Snake2Camel` |
| SnakeCase | PascalCase | `Snake2Pascal` |
| PascalCase | KebabCase | `Pascal2Kebab` |
| KebabCase | PascalCase | `Kebab2Pascal` |
| CamelCase | KebabCase | `Camel2Kebab` |
| KebabCase | CamelCase | `Kebab2Camel` |
| SnakeCase | KebabCase | `Snake2Kebab` |
| KebabCase | SnakeCase | `Kebab2Snake` |

## Unicode 分类

### 基础分类

```go
// 判断是否全为数字
stringx.AllDigit("123")    // true
stringx.AllDigit("12a3")   // false

// 判断是否包含字母
stringx.HasLetter("abc123")  // true
stringx.HasLetter("123")     // false

// 判断是否全为字母
stringx.AllLetter("abc")  // true
stringx.AllLetter("ab1")  // false
```

### 中文字符检测

```go
// 判断是否全为中文
stringx.AllChinese("你好")  // true
stringx.AllChinese("hello") // false

// 判断是否包含中文
stringx.HasChinese("你好hello")  // true
stringx.HasChinese("hello")      // false
```

### 空白字符检测

```go
// 判断是否全为空白
stringx.AllBlank("   \t\n")  // true
stringx.AllBlank("  a  ")    // false

// 判断是否包含空白
stringx.HasBlank("a b")   // true
stringx.HasBlank("ab")    // false

// 判断是否全为空格
stringx.AllSpace("   ")   // true
stringx.AllSpace(" \t ")  // false
```

### 大小写检测

```go
// 判断是否全为小写
stringx.AllLower("abc")  // true
stringx.AllLower("Abc")  // false

// 判断是否全为大写
stringx.AllUpper("ABC")  // true
stringx.AllUpper("Abc")  // false

// 判断是否首字母大写
stringx.IsTitleCase("Hello")  // true
stringx.IsTitleCase("hello")  // false
```

### 可打印字符检测

```go
// 判断是否全为可打印字符
stringx.AllPrintable("abc123")  // true
stringx.AllPrintable("ab\tc")   // false

// 判断是否包含不可打印字符
stringx.HasNonPrintable("ab\tc")  // true
stringx.HasNonPrintable("abc")    // false
```

### 其他分类函数

```go
// 数字相关
stringx.AllNumeric("123.45")   // true（包含小数点）
stringx.HasNumeric("a1b2")     // true

// 控制字符
stringx.AllControl("\n\t")     // true
stringx.HasControl("a\nb")     // true

// 标点符号
stringx.AllPunctuation(".,!")  // true
stringx.HasPunctuation("a.b")  // true

// 符号字符
stringx.AllSymbol("@#$")       // true
stringx.HasSymbol("a@b")       // true

// 十六进制
stringx.AllHexadecimal("1a2B3c")  // true
stringx.HasHexadecimal("1g")      // false
```

### 完整分类函数列表

```
AllDigit, AllLetter, AllLower, AllUpper
AllChinese, HasChinese
AllBlank, HasBlank, AllSpace, HasSpace
AllPrintable, HasNonPrintable
AllNumeric, HasNumeric
AllControl, HasControl
AllPunctuation, HasPunctuation
AllSymbol, HasSymbol
AllHexadecimal, HasHexadecimal
AllASCII, HasNonASCII
AllAlphanumeric, HasNonAlphanumeric
IsTitleCase
```

## 随机字符串生成

### 字母数字

```go
// 生成随机字母数字字符串（默认 16 位）
s := stringx.RandomAlphanumeric()
// "aB3xY9pL2mQ4vZ6"

// 指定长度
s := stringx.RandomAlphanumeric(32)
```

### 字母

```go
// 生成随机字母字符串（默认 16 位）
s := stringx.RandomLetters()
// "aBxYpLmQvZkHrG"

// 指定长度
s := stringx.RandomLetters(20)
```

### 数字

```go
// 生成随机数字字符串（默认 16 位）
s := stringx.RandomNumbers()
// "1234567890123456"

// 指定长度
s := stringx.RandomNumbers(8)
```

### 十六进制

```go
// 生成随机十六进制字符串（默认 16 位）
s := stringx.RandomHex()
// "1a2b3c4d5e6f7a8b"

// 指定长度
s := stringx.RandomHex(32)
```

### 自定义字符集

```go
// 使用自定义字符集
charset := "abcdef0123456789"
s := stringx.RandomString(16, charset)
// "3d7a1b9c5e2f4a6"
```

### UUID 格式

```go
// 生成 UUID 格式字符串（带连字符）
s := stringx.RandomUUID()
// "550e8400-e29b-41d4-a716-446655440000"
```

## 字符串操作

### 反转字符串

```go
// 反转字符串
s := stringx.Reverse("hello")
// "olleh"
```

### 缩短字符串

```go
// 缩短字符串（添加省略号）
s := stringx.Shorten("This is a very long string", 10)
// "This is..."

// 保留前 N 个字符
s := stringx.Shorten("Hello World", 5)
// "Hello"

// 空格处截断（保留完整单词）
s := stringx.ShortenAtSpace("This is a long string", 10)
// "This is..."
```

### 分割字符串

```go
// 分割字符串（去除空项）
parts := stringx.Split("a,b,,c", ",")
// ["a", "b", "c"]

// 保留空项
parts := strings.Split("a,b,,c", ",")
// ["a", "b", "", "c"]
```

## 标准库包装

为了方便使用，stringx 也包装了部分标准库函数：

```go
// TrimSpace 包装
s := stringx.TrimSpace("  hello  ")
// "hello"

// ToLower 包装
s := stringx.ToLower("HELLO")
// "hello"

// ToUpper 包装
s := stringx.ToUpper("hello")
// "HELLO"

// Contains 包装
ok := stringx.Contains("hello", "ell")
// true

// HasPrefix 包装
ok := stringx.HasPrefix("hello", "he")
// true

// HasSuffix 包装
ok := stringx.HasSuffix("hello", "lo")
// true
```

## 最佳实践

### 1. 性能敏感场景

```go
// ❌ 标准库（有拷贝）
for i := 0; i < 1000000; i++ {
    b := []byte(s)
    // 处理 b
}

// ✅ 零拷贝转换
for i := 0; i < 1000000; i++ {
    b := stringx.ToBytes(s)
    // 处理 b（只读）
}
```

### 2. 命名转换

```go
// JSON 标签生成
fieldName := "UserID"
jsonTag := fmt.Sprintf("`json:\"%s\"`", stringx.Camel2Snake(fieldName))
// `json:"user_id"`

// 数据库列名
columnName := stringx.Camel2Snake("ProfileImageURL")
// "profile_image_url"
```

### 3. 输入验证

```go
// 用户名验证（只允许字母数字）
if !stringx.AllAlphanumeric(username) {
    return errors.New("invalid username")
}

// 密码强度检查（包含数字）
if !stringx.HasNumeric(password) {
    return errors.New("password must contain numbers")
}
```

### 4. 随机字符串

```go
// Session ID
sessionID := stringx.RandomAlphanumeric(32)

// 验证码
code := stringx.RandomNumbers(6)

// 临时文件名
tempFile := stringx.RandomHex(16) + ".tmp"
```

## 性能基准

```
BenchmarkToString-8          100000000    10.1 ns/op    0 B/op    0 allocs/op
BenchmarkToBytes-8           100000000    10.2 ns/op    0 B/op    0 allocs/op
BenchmarkCamel2Snake-8       10000000     128 ns/op     64 B/op    2 allocs/op
BenchmarkAllDigit-8          50000000      32.1 ns/op    0 B/op    0 allocs/op
BenchmarkRandomAlphanumeric-8 2000000     612 ns/op     32 B/op    1 allocs/op
```

## 参考资源

- [lazygophers/utils/stringx GitHub](https://github.com/lazygophers/utils/tree/main/stringx)
