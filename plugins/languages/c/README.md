# C 开发插件

C 开发插件提供高质量的 C 代码开发指导和 LSP 支持。包括 C11/C17 标准、系统编程、嵌入式开发和 POSIX API 规范。

## 功能特性

### 核心功能

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

## 安装

### 前置条件

1. **clangd 安装**

```bash
# macOS
brew install llvm

# Linux (Ubuntu/Debian)
apt install clangd

# 验证安装
which clangd
clangd --version
```

2. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/languages/c

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/languages/c ~/.claude/plugins/
```

## 项目结构

```
c/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（clangd）
├── agents/
│   ├── dev.md                           # 开发专家代理
│   ├── test.md                          # 测试专家代理
│   ├── debug.md                         # 调试专家代理
│   └── perf.md                          # 性能优化代理
├── skills/c-skills/
│   ├── SKILL.md                         # 核心规范入口
│   ├── development-practices.md         # 内存管理、指针、字符串
│   ├── system-programming.md            # POSIX API、进程、线程
│   ├── embedded-development.md          # 寄存器、中断、约束优化
│   ├── specialized/                     # 高级主题
│   │   ├── posix-api.md                 # POSIX API 详解
│   │   ├── memory-management.md         # 内存管理详解
│   │   └── concurrency.md               # 并发编程
│   └── references.md                    # 参考资料
├── hooks/hooks.json                     # Hook 配置
├── scripts/
│   ├── main.py                          # CLI 入口
│   └── hooks.py                         # Hook 处理
└── README.md                            # 本文档
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

### 官方文档

- [cppreference C](https://en.cppreference.com/w/c/) - C 语言参考
- [GNU C Library](https://www.gnu.org/software/libc/manual/) - glibc 文档

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：1.0.0
**最后更新**：2026-02-09
