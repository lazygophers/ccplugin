# 代码格式规范

## 基本原则

使用自动化格式化工具（clang-format）确保代码风格一致。

## clang-format 配置

```yaml
# .clang-format
BasedOnStyle: Google
IndentWidth: 4
TabWidth: 4
ColumnLimit: 100
UseTab: Never

# 指针对齐
DerivePointerAlignment: false
PointerAlignment: Left

# 命名空间
NamespaceIndentation: None

# 花括号
BreakBeforeBraces: Attach

# 函数
AllowShortFunctionsOnASingleLine: Empty
BinPackArguments: false
BinPackParameters: false

# 模板
AlwaysBreakTemplateDeclarations: Yes
```

## 缩进

```cpp
// ✅ 4 空格缩进
class MyClass {
public:
    void method() {
        if (condition) {
            do_something();
        }
    }
};

// ✅ 续行缩进
void long_function_name(int parameter1,
                        int parameter2,
                        int parameter3) {
    // 实现
}

// ✅ 链式调用
auto result = object
    .method1()
    .method2()
    .method3();
```

## 花括号

```cpp
// ✅ 附加式
if (condition) {
    do_something();
}

// ✅ 单语句也使用花括号（推荐）
if (condition) {
    do_something();
}

// ✅ 函数
void function() {
    // 实现
}

// ✅ 类
class MyClass {
public:
    // ...
};
```

## 空行

```cpp
// ✅ 函数间空一行
void func1() {
    // ...
}

void func2() {
    // ...
}

// ✅ 逻辑分组空两行
// 配置加载
load_config();

// 数据初始化
init_data();

// 主循环
run_loop();
```

## 行长度

```cpp
// ✅ 保持 < 100 字符（或项目约定）
int result = some_function_with_long_name(parameter1, parameter2);

// ✅ 必要时分行
int result = some_function_with_long_name(
    parameter1,
    parameter2,
    parameter3
);

// ✅ 链式调用分行
auto result = builder
    .set_option1(value1)
    .set_option2(value2)
    .build();
```

## 注释

```cpp
// ✅ 单行注释
// 这是单行注释

// ✅ 行尾注释
int value = 42;  // 初始值

/**
 * @brief 多行注释（Doxygen 风格）
 *
 * 详细说明
 *
 * @param param1 参数1说明
 * @return 返回值说明
 */
int function(int param1);

/// @brief 单行 Doxygen 注释
/// @param x 参数说明
/// @return 返回值说明
int square(int x);
```

## 模板格式

```cpp
// ✅ 简单模板单行
template<typename T>
class Vector { };

// ✅ 复杂模板换行
template<
    typename T,
    typename U = void,
    std::enable_if_t<std::is_integral_v<T>, int> = 0
>
void process(T value);

// ✅ 模板参数
auto result = function<int, std::string, CustomAllocator>();
```

## Lambda 格式

```cpp
// ✅ 单行 lambda
auto result = std::ranges::find_if(vec, [](int x) { return x > 0; });

// ✅ 多行 lambda
auto predicate = [](int x) {
    if (x < 0) return false;
    if (x > 100) return false;
    return true;
};

// ✅ 捕获列表
auto result = [capture1, &capture2](int param) {
    return capture1 + capture2 + param;
};
```

---

**最后更新**：2026-02-09
