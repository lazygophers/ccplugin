---
name: macros
description: Rust 宏开发规范：声明宏、过程宏、derive 宏。开发宏时必须加载。
---

# Rust 宏开发规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | Rust 2024 edition、强制约定 |

## 声明宏

```rust
// 基本宏
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
    ($name:expr) => {
        println!("Hello, {}!", $name);
    };
}

say_hello!();
say_hello!("World");
```

## 过程宏

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyDerive)]
pub fn my_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl MyTrait for #name {
            fn my_method(&self) {
                println!("Generated for {}", stringify!(#name));
            }
        }
    };

    TokenStream::from(expanded)
}
```

## 属性宏

```rust
#[proc_macro_attribute]
pub fn my_attribute(attr: TokenStream, item: TokenStream) -> TokenStream {
    // 处理属性和项
    item
}
```

## 检查清单

- [ ] 宏命名清晰
- [ ] 文档化宏用法
- [ ] 提供良好的错误信息
- [ ] 测试宏展开
