# Rust 宏开发规范

## 核心原则

### ✅ 必须遵守

1. **优先使用宏** - 避免重复代码
2. **声明宏优先** - 优先使用 macro_rules!
3. **过程宏谨慎** - 仅在必要时使用
4. **文档完整** - 宏必须有完整文档和示例
5. **错误友好** - 提供清晰的错误信息

## 声明宏

### 基本 macro_rules!

```rust
// ✅ 简单的声明宏
macro_rules! vec {
    ( $( $x:expr ),* $(,)? ) => {
        {
            let mut temp_vec = Vec::new();
            $(
                temp_vec.push($x);
            )*
            temp_vec
        }
    };
}

// ✅ 使用宏
let v = vec![1, 2, 3];

// ✅ 模式匹配
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
    ($name:expr) => {
        println!("Hello, {}!", $name);
    };
    ($name:expr, $greeting:expr) => {
        println!("{}, {}!", $greeting, $name);
    };
}
```

### 高级模式

```rust
// ✅ 重复模式
macro_rules! find_min {
    ($x:expr) => ($x);
    ($x:expr, $($xs:expr),+) => (
        std::cmp::min($x, find_min!($($xs),+))
    );
}

// ✅ 标识符修改
macro_rules! create_struct {
    ($name:ident { $($field:ident: $type:ty),* $(,)? }) => {
        struct $name {
            $( $field: $type ),*
        }

        impl $name {
            fn new( $( $field: $type ),* ) -> Self {
                Self {
                    $( $field ),*
                }
            }
        }
    };
}

// ✅ 使用宏
create_struct!(User {
    name: String,
    age: u32,
});
```

## 过程宏

### 函数式过程宏

```rust
// ✅ 函数式过程宏
use proc_macro::TokenStream;

#[proc_macro]
pub fn make_answer(input: TokenStream) -> TokenStream {
    // 解析输入
    // 生成输出
    "fn answer() -> u32 { 42 }".parse().unwrap()
}

// ✅ 使用宏
make_answer!();
```

### 派生宏

```rust
// ✅ 自定义派生宏
#[proc_macro_derive(Answer)]
pub fn answer_derive(input: TokenStream) -> TokenStream {
    // 解析输入
    // 生成 impl 块
}

// ✅ 使用宏
#[derive(Answer)]
struct MyStruct;
```

### 属性宏

```rust
// ✅ 属性宏
#[proc_macro_attribute]
pub fn log_function(attr: TokenStream, item: TokenStream) -> TokenStream {
    // 解析属性和项
    // 生成带日志的函数
}

// ✅ 使用宏
#[log_function]
fn my_function() {
    // ...
}
```

## 最佳实践

### 宏设计

```rust
// ✅ 清晰的宏设计
macro_rules! impl_ops {
    ($struct_name:ident, $inner_type:ty) => {
        impl std::ops::Deref for $struct_name {
            type Target = $inner_type;

            fn deref(&self) -> &Self::Target {
                &self.0
            }
        }

        impl std::ops::DerefMut for $struct_name {
            fn deref_mut(&mut self) -> &mut Self::Target {
                &mut self.0
            }
        }
    };
}

// ✅ 使用宏
struct MyVec(Vec<i32>);

impl_ops!(MyVec, Vec<i32>);
```

### 错误处理

```rust
// ✅ 友好的错误信息
macro_rules! check_type {
    ($value:expr, $type:ty) => {
        {
            let value = $value;
            if !value.is::<$type>() {
                panic!(
                    "Expected type `{}`, but found `{}`",
                    std::any::type_name::<$type>(),
                    value.type_name()
                );
            }
            value
        }
    };
}
```

## 检查清单

- [ ] 宏有完整文档
- [ ] 宏有使用示例
- [ ] 错误信息清晰
- [ ] 避免宏卫生问题
- [ ] 测试覆盖宏的所有模式
