---
description: "C++ core conventions: C++20/23 language features, coding standards, best practices, modern idioms. Load before writing or reviewing any C++ code."
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C++ Core Conventions (C++20/23)

## Applicable Agents

| Agent | When |
|---|---|
| Skills(cpp:dev) | All C++ development |
| Skills(cpp:debug) | Debugging with modern idioms |
| Skills(cpp:test) | Writing test code |
| Skills(cpp:perf) | Performance-critical code |

## Related Skills

| Scenario | Skill | Description |
|---|---|---|
| Memory | Skills(cpp:memory) | Smart pointers, RAII, scope guards |
| Concurrency | Skills(cpp:concurrency) | jthread, coroutines, atomics |
| Templates | Skills(cpp:template) | Concepts, CTAD, fold expressions |
| Tooling | Skills(cpp:tooling) | CMake 3.30+, clang-tidy, sanitizers |
| Performance | Skills(cpp:performance) | Cache, SIMD, zero-copy |

## Mandatory Rules

1. **C++20/23 features first** -- use concepts, ranges, std::expected, std::format, std::print
2. **RAII everywhere** -- std::unique_ptr, std::shared_ptr, custom deleters, scope guards
3. **No raw new/delete** -- use std::make_unique, std::make_shared
4. **Value semantics** -- prefer move semantics, copy elision (NRVO)
5. **Concepts over SFINAE** -- constrain all templates with concepts
6. **Ranges over raw loops** -- std::ranges::sort, views::filter, views::transform
7. **std::expected for errors** -- reserve exceptions for truly exceptional cases
8. **Three-way comparison** -- `auto operator<=>(const T&) const = default;`
9. **std::format/std::print** -- no printf, no iostream formatting
10. **No macros** -- use constexpr, consteval, inline, concepts

## Prohibited

- C-style casts (use static_cast, const_cast, reinterpret_cast, std::bit_cast)
- malloc/free (use smart pointers)
- Raw owning pointers (use std::unique_ptr/std::shared_ptr)
- C-style arrays (use std::array, std::vector, std::span)
- varargs (use variadic templates with fold expressions)
- Macros for constants/functions (use constexpr, consteval)
- RTTI unless absolutely necessary

## C++20 Features

| Feature | Usage | Example |
|---|---|---|
| Concepts | Constrain templates | `template<std::integral T>` |
| Ranges | Functional pipelines | `data \| views::filter(pred) \| views::transform(fn)` |
| Coroutines | Async/generators | `co_await`, `co_yield`, `co_return` |
| Modules | Replace headers | `import std;` `export module mylib;` |
| Three-way comparison | Auto-generate operators | `auto operator<=>(const T&) const = default;` |
| std::format | Type-safe formatting | `std::format("{:.2f}", 3.14)` |
| std::span | Non-owning view | `void process(std::span<const int> data)` |
| std::jthread | Auto-joining thread | `std::jthread t(func);` |
| std::latch/barrier | Synchronization | `std::latch done(n);` |

## C++23 Features

| Feature | Usage | Example |
|---|---|---|
| std::expected | Error handling | `std::expected<int, Error> parse(str)` |
| std::print | Simple output | `std::print("Hello {}!\n", name)` |
| std::mdspan | Multi-dim view | `std::mdspan<float, std::extents<int, 3, 3>> mat(data)` |
| std::generator | Lazy sequences | `std::generator<int> range(int n)` |
| Deducing this | Recursive lambdas, CRTP | `void f(this auto&& self)` |
| if consteval | Compile-time branch | `if consteval { ... } else { ... }` |
| std::flat_map | Cache-friendly map | `std::flat_map<K, V> m;` |

## C++26 Features (Finalized March 2026)

| Feature | Usage | Example | Compiler |
|---|---|---|---|
| Static Reflection | Compile-time introspection | `constexpr auto members = std::meta::members_of(^MyClass);` | GCC 15+, Clang 19+ (experimental) |
| Contracts | Pre/postconditions | `void f(int x) [[pre: x > 0]] [[post r: r >= 0]]` | GCC 15+, Clang 19+ (experimental) |
| std::execution | Unified async framework | `auto result = co_await on(scheduler, async_work());` | GCC 15+ (partial) |
| SIMD Types | Portable vectorization | `std::simd<float, 4> vec = {1, 2, 3, 4};` | GCC 15+, Clang 19+ |
| Parallel Ranges | Multi-threaded ranges | `ranges::sort(par_unseq, data);` | Experimental |

## Red Flags

| Rationalization | Actual Check |
|---|---|
| "Raw pointers are faster" | Use unique_ptr -- zero overhead |
| "SFINAE works fine" | Use concepts -- clearer errors |
| "printf is simpler" | Use std::format/std::print |
| "Don't need ranges" | Use ranges pipeline over raw loops |
| "C cast is shorter" | Use static_cast/bit_cast |
| "Macros are convenient" | Use constexpr/consteval |

## Checklist

- [ ] C++20/23 features used where applicable
- [ ] All resources managed by RAII (smart pointers, scope guards)
- [ ] Templates constrained with concepts
- [ ] Ranges/algorithms used over raw loops
- [ ] std::expected for expected errors
- [ ] std::format/std::print for output
- [ ] Three-way comparison for custom types
- [ ] No C-style casts, no macros, no raw new/delete
- [ ] Files under 600 lines (200-400 recommended)
