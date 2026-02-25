# C 开发插件

> C 开发插件提供高质量的 C 代码开发指导和 LSP 支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin c@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install c@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **C 开发专家代理** - 提供专业的 C 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 系统编程支持

- **开发规范指导** - 完整的现代 C 开发规范
  - C11/C17 新特性
  - 内存管理和指针
  - POSIX API
  - 嵌入式开发

- **代码智能支持** - 通过 clangd LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | C 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | C 核心规范 |
| Skill | `memory` | 内存管理规范 |
| Skill | `error` | 错误处理规范 |
| Skill | `concurrency` | 并发编程规范 |
| Skill | `embedded` | 嵌入式开发规范 |
| Skill | `posix` | POSIX API 规范 |

## 前置条件

### clangd 安装

```bash
# macOS
brew install llvm

# Linux (Ubuntu/Debian)
apt install clangd

# 验证安装
which clangd
clangd --version
```

## 核心规范

### 必须遵守

1. **标准遵循** - 遵循 C11/C17 标准
2. **内存安全** - 检查 malloc 返回值，避免泄漏
3. **错误检查** - 检查所有系统调用返回值
4. **const 正确性** - 正确使用 const
5. **资源管理** - 确保资源被释放

### 禁止行为

- 不检查 malloc 返回值
- 使用未初始化变量
- 缓冲区溢出
- 使用危险函数（strcpy、sprintf）
- 忽略函数返回值

## 最佳实践

### 内存管理

```c
// ✅ 检查返回值
int* arr = malloc(n * sizeof(int));
if (arr == NULL) {
    fprintf(stderr, "Allocation failed\n");
    exit(EXIT_FAILURE);
}

// ✅ 释放后置空
free(arr);
arr = NULL;
```

### 错误处理

```c
// ✅ 使用 goto 清理
int process(void) {
    FILE* file = NULL;
    char* buffer = NULL;

    file = fopen("data.txt", "r");
    if (file == NULL) goto error;

    buffer = malloc(1024);
    if (buffer == NULL) goto error;

    // 处理
    free(buffer);
    fclose(file);
    return 0;

error:
    if (buffer) free(buffer);
    if (file) fclose(file);
    return -1;
}
```

## 参考资源

- [cppreference C](https://en.cppreference.com/w/c/) - C 语言参考
- [GNU C Library](https://www.gnu.org/software/libc/manual/) - glibc 文档

## 许可证

AGPL-3.0-or-later
