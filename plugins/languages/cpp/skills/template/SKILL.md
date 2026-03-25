---
description: C++ template programming -- concepts, CTAD, fold expressions, constexpr/consteval, variable templates. Load when writing generic code.
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Template Programming (C++20/23)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | Generic library design |
| Skills(cpp:perf) | Compile-time optimization |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Core | Skills(cpp:core) | C++20/23 standards |
| Performance | Skills(cpp:performance) | Compile-time computation |

## Concepts (C++20) -- Always Use

### Standard library concepts

```cpp
#include <concepts>

template<std::integral T>
T gcd(T a, T b) { return b == 0 ? a : gcd(b, a % b); }

template<std::floating_point T>
T lerp(T a, T b, T t) { return a + t * (b - a); }

template<std::ranges::range R>
void process(R&& range) { /* ... */ }
```

### Custom concepts

```cpp
template<typename T>
concept Serializable = requires(T t, std::ostream& os) {
    { t.serialize(os) } -> std::same_as<void>;
    { T::deserialize(os) } -> std::same_as<T>;
};

template<typename T>
concept Container = requires(T t) {
    typename T::value_type;
    { t.begin() } -> std::input_or_output_iterator;
    { t.end() } -> std::sentinel_for<decltype(t.begin())>;
    { t.size() } -> std::convertible_to<std::size_t>;
};

template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

// Compound concepts
template<typename T>
concept SerializableContainer = Container<T> && Serializable<T>;
```

### Concept usage forms

```cpp
// 1. Requires clause
template<typename T> requires Numeric<T>
T add(T a, T b) { return a + b; }

// 2. Abbreviated (preferred for simple cases)
template<Numeric T>
T multiply(T a, T b) { return a * b; }

// 3. Trailing requires
template<typename T>
T divide(T a, T b) requires Numeric<T> { return a / b; }

// 4. Auto with concept (terse syntax)
Numeric auto square(Numeric auto x) { return x * x; }
```

## CTAD (Class Template Argument Deduction)

```cpp
// Automatic deduction
std::pair p{1, 3.14};           // pair<int, double>
std::vector v{1, 2, 3};         // vector<int>
std::optional o{42};             // optional<int>
std::tuple t{1, "hello", 3.14}; // tuple<int, const char*, double>

// Custom deduction guide
template<typename T>
struct Wrapper {
    T value;
};
template<typename T>
Wrapper(T) -> Wrapper<T>;

Wrapper w{42};  // Wrapper<int>
```

## Fold Expressions (C++17)

```cpp
// Unary folds
template<typename... Args>
auto sum(Args... args) { return (args + ...); }

template<typename... Args>
bool all(Args... args) { return (args && ...); }

template<typename... Args>
void print_all(Args&&... args) {
    (std::print("{} ", args), ...);
    std::print("\n");
}

// Binary fold with init
template<typename... Args>
auto sum_with_init(Args... args) { return (args + ... + 0); }
```

## constexpr / consteval / if consteval

```cpp
// constexpr: may run at compile-time or runtime
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}
static_assert(factorial(5) == 120);

// consteval: must run at compile-time (C++20)
consteval int compile_only(int n) {
    return n * n;
}
constexpr int x = compile_only(5);  // OK: 25
// int y = compile_only(runtime_val); // ERROR: not a constant

// if consteval: compile-time branch (C++23)
constexpr int smart(int n) {
    if consteval {
        return heavy_computation(n);  // compile-time: optimize freely
    } else {
        return lookup_table[n];       // runtime: use cached result
    }
}
```

## Variable Templates

```cpp
template<typename T>
inline constexpr bool is_numeric_v = std::integral<T> || std::floating_point<T>;

template<typename T>
inline constexpr size_t cache_line_aligned_size =
    (sizeof(T) + std::hardware_destructive_interference_size - 1)
    / std::hardware_destructive_interference_size
    * std::hardware_destructive_interference_size;
```

## Deducing This (C++23)

```cpp
struct Widget {
    // Deduce value category -- replaces CRTP for many cases
    void process(this auto&& self) {
        if constexpr (std::is_lvalue_reference_v<decltype(self)>) {
            // lvalue: copy
        } else {
            // rvalue: move
        }
    }

    // Recursive lambda
    auto make_visitor() {
        return [](this auto&& self, auto&& variant) {
            std::visit(self, variant);
        };
    }
};
```

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "SFINAE works fine" | Use concepts -- clearer errors, simpler code |
| "Don't need constraints" | Constrain every template with a concept |
| "Explicit types are fine" | Use CTAD where it improves readability |
| "Runtime computation is ok" | Is constexpr/consteval applicable? |
| "Macros for generics" | Use templates with concepts |
| "enable_if is standard" | Use concepts and requires clauses |

## Checklist

- [ ] All templates constrained with concepts
- [ ] Custom concepts for domain abstractions
- [ ] CTAD used where it improves readability
- [ ] Fold expressions for variadic templates
- [ ] constexpr for compile-time-eligible functions
- [ ] consteval for must-be-compile-time functions
- [ ] if consteval for dual compile/runtime paths (C++23)
- [ ] Deducing this for value-category-aware methods (C++23)
- [ ] No SFINAE (replaced by concepts)
- [ ] No enable_if (replaced by requires)
