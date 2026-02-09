# Rust 代码格式规范

## 核心原则

### ✅ 必须遵守

1. **使用 rustfmt** - 自动格式化工具
2. **默认配置** - 使用标准 rustfmt 配置
3. **行长度** - 最大 100 字符（默认）
4. **缩进** - 4 个空格（硬编码）
5. **大括号** - 左大括号在同一行
6. **尾随逗号** - 多行结构体/枚举使用尾随逗号

### rustfmt 配置

```toml
# rustfmt.toml
max_width = 100
hard_tabs = false
tab_spaces = 4
newline_style = "Unix"
use_small_heuristics = "Default"
reorder_imports = true
reorder_modules = true
remove_nested_parens = true
edition = "2024"
merge_derives = true
use_try_shorthand = true
use_field_init_shorthand = true
force_explicit_abi = true
format_code_in_doc_comments = true
normalize_comments = true
normalize_doc_attributes = true
license_template_path = ""
format_strings = true
```

## 代码格式

### 结构体

```rust
// ✅ 单行格式
struct Point {
    x: i32,
    y: i32,
}

// ✅ 多行格式（字段多时）
struct User {
    id: u64,
    name: String,
    email: String,
    status: UserStatus,
    created_at: DateTime<Utc>,
}

// ✅ 元组结构体
struct Color(u8, u8, u8);

// ✅ 单字段元组结构体（新类型模式）
struct UserId(u64);

// ✅ 单元结构体
struct Unit;
```

### 枚举

```rust
// ✅ 单行格式
enum Option<T> {
    Some(T),
    None,
}

// ✅ 多行格式（变体多时）
enum HttpStatus {
    Ok,
    MovedPermanently,
    Found,
    BadRequest,
    Unauthorized,
    NotFound,
    InternalServerError,
}

// ✅ 带数据的变体
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}
```

### 函数

```rust
// ✅ 标准格式
fn add(a: i32, b: i32) -> i32 {
    a + b
}

// ✅ 单行函数
fn add(a: i32, b: i32) -> i32 { a + b }

// ✅ 多行参数
fn process(
    input: &str,
    config: &Config,
    callback: impl FnMut(Result<Data, Error>),
) -> Result<Output, Error> {
    // ...
}

// ✅ 返回类型多行
fn long_function_name(
    param1: Type1,
    param2: Type2,
) -> very::long::ReturnType<
    SomeGenericParam,
    AnotherGenericParam,
> {
    // ...
}
```

### impl 块

```rust
// ✅ 标准 impl 块
impl User {
    fn new(id: u64, name: String) -> Self {
        Self { id, name }
    }

    fn id(&self) -> u64 {
        self.id
    }
}

// ✅ trait impl
impl Display for User {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name)
    }
}
```

### 控制流

### if/else

```rust
// ✅ 标准格式
if condition {
    // ...
} else {
    // ...
}

// ✅ if-let
if let Some(value) = optional {
    // ...
}

// ✅ if-let-chains
if let Some(value) = optional
    && value > 10
{
    // ...
}

// ✅ 单行 if
if condition { return; }

// ✅ 单行 if-else
let result = if condition { 1 } else { 0 };
```

### match

```rust
// ✅ 标准 match
match value {
    Pattern1 => expr1,
    Pattern2 => expr2,
    _ => default_expr,
}

// ✅ 多行 match 分支
match value {
    Pattern1 | Pattern2 => {
        // 多行代码
        expr
    }
    Pattern3 => expr3,
    _ => default_expr,
}

// �️ 尾随逗号
match value {
    Pattern1 => expr1,
    Pattern2 => expr2,
    Pattern3 => expr3,
    _ => default_expr,  // 尾随逗号
}
```

### 循环

```rust
// ✅ for 循环
for item in items {
    // ...
}

// ✅ 迭代器
for (idx, item) in items.iter().enumerate() {
    // ...
}

// ✅ while let
while let Some(value) = optional {
    // ...
}

// ✅ loop
loop {
    // ...
}
```

### 闭包

```rust
// ✅ 单行闭包
let doubled = numbers.iter().map(|x| x * 2).collect::<Vec<_>>();

// ✅ 多行闭包
numbers.iter().for_each(|x| {
    let doubled = x * 2;
    process(doubled);
});

// ✅ move 闭包
let captured = value;
let closure = move || {
    // 使用 captured
};
```

## 导入规范

### use 声明

```rust
// ✅ 标准导入
use std::collections::HashMap;

// ✅ 多个导入
use std::{collections::HashMap, io::Read};

// ✅ 嵌套导入
use std::collections::{
    HashMap,
    HashSet,
};

// ✅ 自导入
use crate::module::Type;
use crate::module::function;
use crate::module::{self as module_alias, Type};

// ✅ 重命名
use std::io::{self as io, Result as IoResult};

// ❌ 避免 - 通配符导入（除非测试）
use std::collections::*;  // 不要使用
```

### 导入顺序

rustfmt 会自动排序导入，通常按以下顺序：

1. 标准库导入
2. 外部 crate 导入
3. 本地 crate/模块导入

```rust
// ✅ rustfmt 自动排序
use std::collections::HashMap;
use std::io::Read;
use serde::{Deserialize, Serialize};
use tokio::runtime::Runtime;
use crate::config::Config;
use crate::module::Type;
```

## 注释规范

### 文档注释

```rust
// ✅ 文档注释（/// 或 //！）
/// 这是一个文档注释。
///
/// # 示例
///
/// ```
/// use my_crate::function;
///
/// let result = function();
/// ```
///
/// # 错误
///
/// 如果输入无效，将返回 `Error::InvalidInput`。
pub fn function() -> Result<(), Error> {
    // ...
}

// ✅ 模块文档（//!）
//! # My Module
//!
//! 这个模块做某事。
```

### 行内注释

```rust
// ✅ 单行注释
let result = calculate();  // 计算结果

// ✅ 代码上方注释
// 检查边界条件
if value > max {
    return Err(Error::OutOfBounds);
}

// ❌ 避免 - 无意义的注释
let x = 1;  // 设置 x 为 1
```

## 宏使用

### 宏格式

```rust
// ✅ vec! 宏
let numbers = vec![1, 2, 3, 4, 5];

// ✅ 多行 vec!
let numbers = vec![
    1, 2, 3, 4, 5,
];

// ✅ 宏调用
println!("Value: {}", value);

// ✅ 多行宏调用
format!(
    "User: {}, Email: {}",
    user.name,
    user.email
);
```

## 检查清单

提交代码前：

- [ ] 代码已格式化（cargo fmt）
- [ ] 使用 rustfmt.toml 配置
- [ ] 行长度不超过 100
- [ ] 多行结构体/枚举有尾随逗号
- [ ] 文档注释完整
- [ ] 使用 rustfmt --check 验证
