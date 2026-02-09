# Rust 命名规范

强调**清晰、一致、符合 Rust 约定**。

## 核心原则

### ✅ 必须遵守

1. **结构体/枚举 PascalCase** - MyStruct、MyEnum
2. **函数/方法 snake_case** - my_function、my_method
3. **常量 UPPER_SNAKE_CASE** - MAX_SIZE、DEFAULT_TIMEOUT
4. **类型参数大写单字母** - T、U、V
5. **生命周期名短小** - 'a、'b、'src
6. **模块名 snake_case** - my_module
7. **特征名 PascalCase 或描述性** - Iterator、IntoIterator

### ❌ 禁止行为

- 混合命名风格
- 无意义的短名（x, y, z）
- 过长的变量名
- 缩写不清楚

## 类型命名

### 结构体

```rust
// ✅ 推荐 - PascalCase
struct MyStruct { }

struct User { }

struct UserService { }

// ✅ 推荐 - 元组结构体
struct Color(u8, u8, u8);

struct Point(i32, i32);

// ❌ 避免 - 其他风格
struct myStruct { }  // 应该是 MyStruct
struct MY_STRUCT { }  // 应该是 MyStruct
```

### 枚举

```rust
// ✅ 推荐 - PascalCase
enum MyEnum {
    Variant1,
    Variant2,
}

enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}

// ✅ 推荐 - 枚举变体 PascalCase
enum HttpStatus {
    Ok,
    NotFound,
    InternalServerError,
}

// ❌ 避免 - SCREAMING_SNAKE_CASE
enum HttpStatus {
    OK,
    NOT_FOUND,
    INTERNAL_SERVER_ERROR,  // 不要使用
}
```

## 函数和方法命名

### 函数

```rust
// ✅ 推荐 - snake_case
fn my_function() { }

fn get_user(id: u64) -> Option<User> { }

fn create_user(req: CreateUserRequest) -> Result<User, Error> { }

fn is_valid(value: &str) -> bool { }

// ✅ 推荐 - 转换函数 from_into_xxx
fn from_bytes(bytes: &[u8]) -> &str { }

// ✅ 推荐 - as_ 转换
fn as_str(&self) -> &str { }

fn as_mut_slice(&mut self) -> &mut [T] { }

// ❌ 避免 - camelCase
fn myFunction() { }  // 应该是 snake_case
```

### 方法

```rust
impl User {
    // ✅ 构造函数 new
    pub fn new(id: u64, name: String) -> Self {
        Self { id, name }
    }

    // ✅ Getter（通常直接暴露字段或使用同名方法）
    pub fn id(&self) -> u64 {
        self.id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    // ✅ is_ 前缀（布尔）
    pub fn is_active(&self) -> bool {
        self.status == Status::Active
    }

    // ✅ has_ 前缀（布尔）
    pub fn has_permission(&self, perm: &str) -> bool {
        self.permissions.contains(perm)
    }

    // ✅ with_ 建造者模式
    pub fn with_name(mut self, name: String) -> Self {
        self.name = name;
        self
    }
}
```

## 变量命名

### 局部变量

```rust
// ✅ 推荐 - snake_case
let user_id = 1;
let user_name = "Alice";
let max_size = 100;

// ✅ 推荐 - 描述性名字
let user = fetch_user(user_id);
let config = load_config();

// ✅ 推荐 - 短名在作用域小时可以
for i in 0..10 { }
for (idx, item) in items.iter().enumerate() { }

// ❌ 避免 - 无意义
let x = 1;
let y = "name";
let temp = get_value();
```

### 布尔变量

```rust
// ✅ 推荐 - is/has 前缀
let is_active = true;
let has_permission = false;
let can_write = true;
let should_retry = false;

// ❌ 避免 - 不清晰
let active = true;  // 应该是 is_active
let permission = true;  // 应该是 has_permission
```

## 常量命名

### 常量和静态变量

```rust
// ✅ 推荐 - UPPER_SNAKE_CASE
const MAX_SIZE: usize = 100;
const DEFAULT_TIMEOUT: u64 = 30;
const BUFFER_SIZE: usize = 8192;

static GLOBAL_CONFIG: &str = "config";

// ✅ 推荐 - 枚举值 PascalCase
enum Status {
    Active,
    Inactive,
    Pending,
}

// ❌ 避免 - 其他风格
const max_size: usize = 100;  // 应该是 MAX_SIZE
static GlobalConfig: &str = "config";  // 应该是 GLOBAL_CONFIG
```

## 类型参数

### 泛型参数

```rust
// ✅ 推荐 - 单个大写字母
fn generic_function<T>(value: T) { }

fn pair<T, U>(first: T, second: U) -> (T, U) {
    (first, second)
}

// ✅ 推荐 - 有意义的缩写
fn process_result<T, E>(result: Result<T, E>) { }

fn key_value<K, V>(key: K, value: V) { }

// ✅ 推荐 - 特定含义
trait Iterator {
    type Item;
}

// ❌ 避免 - 小写或无意义
fn generic_function<t>(value: t) { }  // 应该是大写
fn process_result<Res, Err>(result: Result<Res, Err>) { }  // 太长
```

## 生命周期命名

### 生命周期参数

```rust
// ✅ 推荐 - 短小的小写字母
fn borrow<'a>(s: &'a str) -> &'a str {
    s
}

fn with_both<'a, 'b>(s1: &'a str, s2: &'b str) -> &'a str {
    s1
}

// ✅ 推荐 - 描述性生命周期名
struct Context<'a> {
    data: &'a str,
}

struct StrWithContext<'s, 'ctx> {
    string: &'s str,
    context: &'ctx str,
}

// ❌ 避免 - 过长或无意义
fn borrow<'string>(s: &'string str) -> &'string str { }  // 太长
fn borrow<'a, 'b, 'c, 'd>(...) { }  // 太多生命周期
```

## 模块命名

### 模块和文件

```rust
// ✅ 推荐 - snake_case
mod my_module { }

mod user_service { }

mod api_handlers { }

// 文件名对应
// my_module.rs
// user_service.rs
// api_handlers.rs

// ❌ 避免 - 其他风格
mod myModule { }  // 应该是 snake_case
mod userService { }  // 应该是 user_service
```

## 特征命名

### Trait

```rust
// ✅ 推荐 - PascalCase（通常是动词形式或形容词）
trait Iterator { }

trait IntoIterator { }

trait Display { }

trait From<T> { }

// ✅ 推荐 - 描述性名称
trait Drawable {
    fn draw(&self);
}

trait Serializable {
    fn serialize(&self) -> Vec<u8>;
}

// ❌ 避免 - 其他风格
trait drawable { }  // 应该是 Drawable
trait To_Serialize { }  // 应该是 ToSerialize
```

## 关联类型命名

```rust
// ✅ 推荐 - PascalCase
trait Iterator {
    type Item;
}

trait Graph {
    type Node;
    type Edge;
}

// ✅ 推荐 - 有意义的名称
trait Container {
    type Element;
    type IntoIter: Iterator<Item = Self::Element>;
}
```

## 测试命名

### 测试函数

```rust
// ✅ 推荐 - test_ 前缀或描述性名称
#[test]
fn test_add_two_numbers() { }

#[test]
fn test_add_with_zero() { }

#[test]
fn test_add_overflow_panics() { }

// ✅ 推荐 - 描述性测试名
#[test]
fn user_service_returns_none_for_invalid_id() { }

#[test]
fn user_service_creates_user_successfully() { }

// ❌ 避免 - 不清晰
#[test]
fn test1() { }
#[test]
fn check() { }
```

## 检查清单

提交代码前，确保：

- [ ] 所有结构体/枚举使用 PascalCase
- [ ] 所有函数/方法使用 snake_case
- [ ] 所有常量使用 UPPER_SNAKE_CASE
- [ ] 类型参数使用大写单字母
- [ ] 生命周期名短小
- [ ] 模块名使用 snake_case
- [ ] 测试函数名有描述性
- [ ] 布尔变量使用 is/has 前缀
- [ ] 变量名有意义（不用 x, y, z）
- [ ] 遵循 Rust 命名约定
