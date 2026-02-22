---
name: unsafe
description: Rust Unsafe 开发规范：unsafe 代码、FFI、未定义行为。写 unsafe 代码时必须加载。
---

# Rust Unsafe 开发规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | Rust 2024 edition、强制约定 |
| 内存管理 | Skills(memory) | 智能指针、内存布局 |

## Unsafe 块

```rust
// unsafe 块
unsafe {
    // 解引用裸指针
    let value = *raw_ptr;

    // 调用 unsafe 函数
    unsafe_function();

    // 访问可变静态变量
    STATIC_VAR += 1;
}

// unsafe 函数
unsafe fn dangerous_operation() -> i32 {
    // unsafe 实现
}

// unsafe trait
unsafe trait Trusted {
    fn trusted_method(&self);
}

unsafe impl Trusted for MyType {
    fn trusted_method(&self) {
        // 实现
    }
}
```

## FFI

```rust
// 链接 C 库
#[link(name = "mylib")]
extern "C" {
    fn c_function(arg: i32) -> i32;
}

// 调用 C 函数
unsafe {
    let result = c_function(42);
}
```

## 检查清单

- [ ] 最小化 unsafe 代码
- [ ] 文档化 unsafe 原因
- [ ] 封装 unsafe 为安全 API
- [ ] 测试 unsafe 代码
