---
description: Rust 宏开发规范 - 声明宏、derive 宏、proc-macro2 + syn 2.x + quote。开发宏时加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Rust 宏开发规范

## 适用 Agents

- **rust:dev** - 宏的设计与实现

## 相关 Skills

- **Skills(rust:core)** - Rust 2024 edition、工具链
- **Skills(rust:unsafe)** - 宏生成的 unsafe 代码

## 宏选择决策

| 需求 | 推荐方案 | 说明 |
|------|---------|------|
| 简单重复模式 | 声明宏 `macro_rules!` | 最简单、编译最快 |
| 自动实现 trait | derive 宏 | `#[derive(MyTrait)]` |
| 修改函数/结构体 | 属性宏 | `#[my_attr]` |
| 函数式语法 | 函数式过程宏 | `my_macro!(...)` |
| **优先考虑** | 泛型 + trait | 能用类型系统解决就不用宏 |

## 声明宏（macro_rules!）

```rust
// 基础模式匹配
macro_rules! hashmap {
    ($($key:expr => $value:expr),* $(,)?) => {{
        let mut map = ::std::collections::HashMap::new();
        $(map.insert($key, $value);)*
        map
    }};
}

let m = hashmap! {
    "name" => "Alice",
    "role" => "admin",
};

// 递归宏
macro_rules! count {
    () => { 0usize };
    ($head:tt $($tail:tt)*) => { 1usize + count!($($tail)*) };
}

// 卫生性：使用完整路径
macro_rules! new_vec {
    ($($elem:expr),*) => {
        {
            let mut v = ::std::vec::Vec::new();
            $(v.push($elem);)*
            v
        }
    };
}
```

## Derive 宏（proc-macro2 + syn 2.x + quote）

```rust
// Cargo.toml
// [lib]
// proc-macro = true
//
// [dependencies]
// proc-macro2 = "1"
// syn = { version = "2", features = ["full"] }
// quote = "1"

use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, Data, Fields};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = syn::Ident::new(
        &format!("{name}Builder"),
        name.span(),
    );

    let fields = match &input.data {
        Data::Struct(data) => match &data.fields {
            Fields::Named(fields) => &fields.named,
            _ => panic!("Builder only supports named fields"),
        },
        _ => panic!("Builder only supports structs"),
    };

    let builder_fields = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! { #name: Option<#ty> }
    });

    let setters = fields.iter().map(|f| {
        let name = &f.ident;
        let ty = &f.ty;
        quote! {
            pub fn #name(mut self, value: #ty) -> Self {
                self.#name = Some(value);
                self
            }
        }
    });

    let expanded = quote! {
        pub struct #builder_name {
            #(#builder_fields,)*
        }

        impl #name {
            pub fn builder() -> #builder_name {
                #builder_name {
                    #(#(#fields.ident): None,)*
                }
            }
        }

        impl #builder_name {
            #(#setters)*
        }
    };

    TokenStream::from(expanded)
}
```

## 属性宏

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, ItemFn};

#[proc_macro_attribute]
pub fn timed(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let name = &input.sig.ident;
    let block = &input.block;
    let sig = &input.sig;
    let vis = &input.vis;

    let expanded = quote! {
        #vis #sig {
            let _start = ::std::time::Instant::now();
            let _result = (|| #block)();
            ::tracing::info!(
                function = stringify!(#name),
                elapsed_ms = _start.elapsed().as_millis(),
                "function completed"
            );
            _result
        }
    };

    TokenStream::from(expanded)
}
```

## 宏测试

```rust
// 编译测试（trybuild）
#[test]
fn tests() {
    let t = trybuild::TestCases::new();
    t.pass("tests/expand/*.rs");       // 应该编译通过
    t.compile_fail("tests/fail/*.rs"); // 应该编译失败
}

// 展开验证（cargo-expand）
// cargo expand --test test_name

// 单元测试
#[test]
fn test_hashmap_macro() {
    let m = hashmap! { "a" => 1, "b" => 2 };
    assert_eq!(m.len(), 2);
    assert_eq!(m["a"], 1);
}
```

## Red Flags：AI 常见误区

| AI 可能的解释 | 实际检查 |
|--------------|---------|
| "用宏解决这个问题" | ✅ 是否可用泛型 + trait 替代？ |
| "声明宏够用" | ✅ 复杂场景是否需要过程宏？ |
| "syn 1.x 也行" | ✅ 是否使用 syn 2.x（性能更好）？ |
| "宏错误信息不重要" | ✅ 是否使用 `compile_error!` 提供清晰错误？ |
| "不需要测试宏" | ✅ 是否使用 trybuild 测试编译行为？ |
| "unwrap 在宏里可以" | ✅ 宏是否提供 `span` 精确的错误信息？ |

## 检查清单

- [ ] 优先使用泛型 + trait，宏作为最后手段
- [ ] 声明宏使用完整路径保证卫生性
- [ ] 过程宏使用 syn 2.x + quote
- [ ] 宏提供清晰的编译错误信息
- [ ] 使用 trybuild 测试编译行为
- [ ] 使用 cargo-expand 验证展开结果
- [ ] 文档说明宏的用法和限制
