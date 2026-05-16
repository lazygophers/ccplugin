---
name: rust-macros
description: Rust 宏开发规范 — `macro_rules!` 声明宏（卫生性、完整路径、递归 / 重复模式）、过程宏（derive / 属性 / 函数式）、proc-macro2 + syn 2.x + quote 工具链、trybuild 编译测试、cargo-expand 展开验证、`compile_error!` span 精确报错。设计宏 API、实现 derive 宏、做代码生成 / 元编程时加载。触发短语：macro_rules、proc-macro、derive 宏、属性宏、syn、quote、代码生成、宏展开、元编程。
user-invocable: true
---

# Rust 宏开发规范

前置：`rust-core`。

## 选型决策

| 需求 | 方案 |
|------|------|
| 简单重复模式（DSL） | `macro_rules!` |
| 自动实现 trait | derive 过程宏 |
| 改装函数 / 结构体 | 属性过程宏 |
| 函数式 DSL | 函数式过程宏 |
| **首选** | 泛型 + trait 解决，无法解决再宏 |

宏是代码生成器，不是抽象工具。能用类型系统解决的问题禁止上宏。

## `macro_rules!` 模板

```rust
macro_rules! hashmap {
    ($($k:expr => $v:expr),* $(,)?) => {{
        let mut m = ::std::collections::HashMap::new();
        $(m.insert($k, $v);)*
        m
    }};
}

let m = hashmap! { "a" => 1, "b" => 2, };
```

卫生性铁律：宏内引用 std / 第三方类型必须用 `::std::...` / `::serde::...` 完整路径，避免调用方命名空间污染。

## 过程宏脚手架

`Cargo.toml`：

```toml
[lib]
proc-macro = true

[dependencies]
proc-macro2 = "1"
syn = { version = "2", features = ["full"] }
quote = "1"
```

Derive 宏示例：

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, Data, Fields};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let name = &ast.ident;
    let builder = syn::Ident::new(&format!("{name}Builder"), name.span());

    let fields = match &ast.data {
        Data::Struct(s) => match &s.fields {
            Fields::Named(f) => &f.named,
            _ => return syn::Error::new_spanned(name, "Builder requires named fields")
                .to_compile_error().into(),
        },
        _ => return syn::Error::new_spanned(name, "Builder requires struct")
            .to_compile_error().into(),
    };

    let setters = fields.iter().map(|f| {
        let n = &f.ident; let t = &f.ty;
        quote! { pub fn #n(mut self, v: #t) -> Self { self.#n = Some(v); self } }
    });

    quote! {
        impl #builder {
            #(#setters)*
        }
    }.into()
}
```

属性宏（函数包装）：

```rust
#[proc_macro_attribute]
pub fn timed(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let f = parse_macro_input!(item as syn::ItemFn);
    let sig = &f.sig; let block = &f.block; let vis = &f.vis;
    let name = &sig.ident;
    quote! {
        #vis #sig {
            let _t = ::std::time::Instant::now();
            let _r = (|| #block)();
            ::tracing::info!(fn = stringify!(#name), elapsed_ms = _t.elapsed().as_millis());
            _r
        }
    }.into()
}
```

## 错误处理

宏内部禁止 `panic!`；用 `syn::Error::new_spanned(...).to_compile_error()` 在出错位置给出 IDE 友好提示。

```rust
return syn::Error::new_spanned(field, "expected `#[builder(default)]`")
    .to_compile_error().into();
```

## 测试

```rust
// trybuild：验证编译通过 / 失败
#[test]
fn ui() {
    let t = trybuild::TestCases::new();
    t.pass("tests/expand/*.rs");
    t.compile_fail("tests/fail/*.rs");
}
```

`cargo expand --test <name>` 验证展开结果，作为开发期 review 工具。

## 反模式

| AI 倾向 | 正确做法 |
|---------|---------|
| 万物皆可宏 | 先用泛型 + trait |
| `syn` 1.x | 升级到 `syn` 2.x |
| `panic!` 报错 | `Error::to_compile_error` |
| 宏内裸 `String` | 完整路径 `::std::string::String` |
| 不写测试 | trybuild + cargo expand |

## 检查清单

- [ ] 已尝试泛型 / trait 方案
- [ ] `macro_rules!` 使用 `::` 完整路径
- [ ] proc-macro 使用 `syn` 2.x + `quote`
- [ ] 编译错误用 `syn::Error::to_compile_error` 而非 `panic!`
- [ ] 有 `trybuild` 编译测试
- [ ] 公共宏有文档示例
