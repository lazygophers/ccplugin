---
name: lrpc-osx
description: lazygophers/utils osx 模块完整指南 - 文件操作、路径处理、进程管理和系统信息工具
---

# lrpc-osx 模块指南

> lazygophers/utils 的 osx 模块提供操作系统级别的文件和路径操作工具，简化常见的文件系统操作。

## 目录

- [概述](#概述)
- [模块结构](#模块结构)
- [核心功能](#核心功能)
  - [文件存在性检查](#文件存在性检查)
  - [文件类型判断](#文件类型判断)
  - [文件系统操作](#文件系统操作)
  - [文件复制](#文件复制)
- [API 参考](#api-参考)
- [最佳实践](#最佳实践)
- [注意事项](#注意事项)
- [完整示例](#完整示例)

---

## 概述

osx 模块是 lazygophers/utils 库的基础工具模块，提供：

- **文件存在性检查**：快速判断文件或目录是否存在
- **文件类型判断**：区分文件和目录
- **文件系统操作**：强制重命名、文件复制等
- **抽象文件系统支持**：支持 `fs.FS` 接口

### 主要特点

- **零依赖**：仅使用标准库
- **简洁 API**：函数命名清晰，参数简单
- **错误处理**：提供布尔返回值和错误返回两种方式
- **跨平台**：支持 Windows、Linux、macOS

---

## 模块结构

```
osx/
├── file.go          # 核心实现
└── file_test.go     # 完整测试套件
```

### 导入方式

```go
import "lazygophers/utils/osx"
```

---

## 核心功能

### 文件存在性检查

#### Exists() - 快速存在性检查（已废弃）

```go
func Exists(path string) bool
```

**功能**：检查路径是否存在。

**返回值**：
- `true` - 路径存在
- `false` - 路径不存在

**⚠️ 已知问题**：
此函数存在逻辑错误（第12行应该使用 `!os.IsNotExist(err)`），建议使用 `Exist()` 代替。

**示例**：
```go
if osx.Exists("/tmp/test.txt") {
    fmt.Println("文件存在")
}
```

#### Exist() - 推荐的存在性检查

```go
func Exist(path string) bool
```

**功能**：正确实现的路径存在性检查。

**实现原理**：
```go
func Exist(path string) bool {
    _, err := os.Stat(path)
    if err != nil {
        return false
    }
    return true
}
```

**示例**：
```go
if osx.Exists("/tmp/test.txt") {
    fmt.Println("文件存在")
}
```

---

### 文件类型判断

#### IsDir() - 判断是否为目录

```go
func IsDir(path string) bool
```

**功能**：检查路径是否为目录。

**返回值**：
- `true` - 是目录
- `false` - 不是目录或路径不存在

**实现**：
```go
func IsDir(path string) bool {
    info, err := os.Stat(path)
    if err != nil {
        return false
    }
    return info.IsDir()
}
```

**示例**：
```go
if osx.IsDir("/tmp") {
    fmt.Println("/tmp 是目录")
}
```

#### IsFile() - 判断是否为文件

```go
func IsFile(path string) bool
```

**功能**：检查路径是否为文件。

**返回值**：
- `true` - 是文件
- `false` - 不是文件或路径不存在

**实现**：
```go
func IsFile(path string) bool {
    info, err := os.Stat(path)
    if err != nil {
        return false
    }
    return !info.IsDir()
}
```

**示例**：
```go
if osx.IsFile("/tmp/test.txt") {
    fmt.Println("/tmp/test.txt 是文件")
}
```

---

### 文件系统操作

#### FsHasFile() - 抽象文件系统检查

```go
func FsHasFile(fs fs.FS, path string) bool
```

**功能**：检查抽象文件系统（`fs.FS`）中是否存在指定路径。

**参数**：
- `fs` - 实现 `fs.FS` 接口的文件系统
- `path` - 要检查的路径

**返回值**：
- `true` - 路径存在
- `false` - 路径不存在

**实现**：
```go
func FsHasFile(fs fs.FS, path string) bool {
    f, err := fs.Open(path)
    if err != nil {
        return false
    }
    defer f.Close()
    return true
}
```

**使用场景**：
- 测试中使用 `fstest.MapFS`
- 嵌入式文件系统
- 内存文件系统

**示例**：
```go
import (
    "io/fs"
    "testing/fstest"
)

// 使用 MapFS 测试
testFS := fstest.MapFS{
    "file.txt": &fstest.MapFile{Data: []byte("test content")},
    "dir/file.txt": &fstest.MapFile{Data: []byte("sub content")},
}

if osx.FsHasFile(testFS, "file.txt") {
    fmt.Println("file.txt 存在于测试文件系统中")
}

// 使用真实文件系统
import "os"

fsys := os.DirFS("/tmp")
if osx.FsHasFile(fsys, "test.txt") {
    fmt.Println("test.txt 存在于 /tmp 目录")
}
```

---

#### RenameForce() - 强制重命名

```go
func RenameForce(oldpath, newpath string) error
```

**功能**：强制重命名文件或目录，如果目标已存在则先删除。

**特点**：
- 自动覆盖已存在的目标
- 支持文件和目录
- 原子操作

**实现**：
```go
func RenameForce(oldpath, newpath string) error {
    if Exists(newpath) {
        err := os.RemoveAll(newpath)
        if err != nil {
            return err
        }
    }
    err := os.Rename(oldpath, newpath)
    if err != nil {
        return err
    }
    return nil
}
```

**使用场景**：
- 原子性文件更新
- 目录替换
- 文件移动（覆盖已存在）

**示例**：
```go
// 基本用法
err := osx.RenameForce("/tmp/old.txt", "/tmp/new.txt")
if err != nil {
    log.Fatal(err)
}

// 覆盖已存在的文件
err = osx.RenameForce("/tmp/current.txt", "/tmp/backup.txt")
if err != nil {
    log.Fatal(err)
}

// 重命名目录（包括内容）
err = osx.RenameForce("/tmp/old_dir", "/tmp/new_dir")
if err != nil {
    log.Fatal(err)
}
```

**错误处理**：
```go
err := osx.RenameForce("/tmp/old.txt", "/tmp/new.txt")
if err != nil {
    if os.IsNotExist(err) {
        fmt.Println("源文件不存在")
    } else if os.IsPermission(err) {
        fmt.Println("权限不足")
    } else {
        fmt.Printf("其他错误: %v\n", err)
    }
}
```

---

### 文件复制

#### Copy() - 文件复制

```go
func Copy(src, dst string) error
```

**功能**：复制文件，保留文件权限。

**特点**：
- 保留原始文件权限
- 支持空文件
- 自动覆盖目标文件
- 仅支持文件复制，不支持目录

**实现**：
```go
func Copy(src, dst string) error {
    // 打开源文件
    srcFile, err := os.Open(src)
    if err != nil {
        return err
    }
    defer srcFile.Close()

    // 获取文件信息
    stat, err := srcFile.Stat()
    if err != nil {
        return err
    }

    // 创建目标文件
    dstFile, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, stat.Mode())
    if err != nil {
        return err
    }
    defer dstFile.Close()

    // 复制内容
    _, err = io.Copy(dstFile, srcFile)
    if err != nil {
        return err
    }

    return nil
}
```

**使用场景**：
- 配置文件备份
- 模板文件复制
- 数据文件复制

**示例**：
```go
// 基本用法
err := osx.Copy("/tmp/source.txt", "/tmp/dest.txt")
if err != nil {
    log.Fatal(err)
}

// 复制空文件
err = osx.Copy("/tmp/empty.txt", "/tmp/empty_copy.txt")
if err != nil {
    log.Fatal(err)
}

// 覆盖已存在的文件
err = osx.Copy("/tmp/new.txt", "/tmp/existing.txt")
if err != nil {
    log.Fatal(err)
}
```

**性能考虑**：
- 使用 `io.Copy` 自动缓冲优化
- 支持大文件复制
- 内存占用恒定（32KB 缓冲区）

**限制**：
- 不支持目录递归复制
- 不复制符号链接（会复制链接指向的内容）
- 不保留文件的时间戳（仅保留权限）

---

## API 参考

### 函数清单

| 函数 | 签名 | 返回值 | 说明 |
|------|------|--------|------|
| `Exists` | `func(path string) bool` | `bool` | 检查路径是否存在（已废弃） |
| `Exist` | `func(path string) bool` | `bool` | 检查路径是否存在（推荐） |
| `IsDir` | `func(path string) bool` | `bool` | 检查是否为目录 |
| `IsFile` | `func(path string) bool` | `bool` | 检查是否为文件 |
| `FsHasFile` | `func(fs fs.FS, path string) bool` | `bool` | 检查抽象文件系统中的路径 |
| `RenameForce` | `func(oldpath, newpath string) error` | `error` | 强制重命名/移动 |
| `Copy` | `func(src, dst string) error` | `error` | 复制文件 |

### 性能特征

| 操作 | 时间复杂度 | 空间复杂度 | 说明 |
|------|-----------|-----------|------|
| `Exists/Exist` | O(1) | O(1) | 单次系统调用 |
| `IsDir/IsFile` | O(1) | O(1) | 单次系统调用 |
| `FsHasFile` | O(1) | O(1) | 单次 Open 操作 |
| `RenameForce` | O(1) | O(1) | 原子操作 |
| `Copy` | O(n) | O(1) | n = 文件大小，恒定缓冲区 |

---

## 最佳实践

### 1. 使用正确的存在性检查

```go
// ❌ 错误：使用有 bug 的 Exists
if osx.Exists(path) {
    // 可能导致意外的行为
}

// ✅ 正确：使用 Exist
if osx.Exist(path) {
    // 可靠的结果
}
```

### 2. 操作前检查路径类型

```go
path := "/tmp/test"

if osx.Exist(path) {
    if osx.IsDir(path) {
        fmt.Println("是目录，使用 os.MkdirAll")
    } else if osx.IsFile(path) {
        fmt.Println("是文件，使用 os.WriteFile")
    }
}
```

### 3. 使用 FsHasFile 进行测试

```go
func TestMyFunction(t *testing.T) {
    testFS := fstest.MapFS{
        "config.json": &fstest.MapFile{Data: []byte(`{"key":"value"}`)},
    }

    // 测试代码使用抽象文件系统
    result := osx.FsHasFile(testFS, "config.json")
    if !result {
        t.Fatal("config.json 应该存在")
    }
}
```

### 4. 原子性文件更新

```go
// 使用临时文件 + RenameForce 实现原子更新
tempFile := "/tmp/config.tmp"
finalFile := "/etc/app/config.json"

// 1. 写入临时文件
err := os.WriteFile(tempFile, newConfig, 0644)
if err != nil {
    return err
}

// 2. 原子性替换
err = osx.RenameForce(tempFile, finalFile)
if err != nil {
    os.Remove(tempFile) // 清理临时文件
    return err
}
```

### 5. 错误处理模式

```go
// 完整的错误处理
err := osx.Copy(src, dst)
if err != nil {
    switch {
    case os.IsNotExist(err):
        fmt.Println("源文件不存在")
    case os.IsPermission(err):
        fmt.Println("权限不足")
    case errors.Is(err, syscall.ENOSPC):
        fmt.Println("磁盘空间不足")
    default:
        fmt.Printf("未知错误: %v\n", err)
    }
}
```

---

## 注意事项

### 已知问题

#### 1. Exists() 函数的 Bug

**问题**：`Exists()` 函数在第 12 行使用了错误的逻辑：

```go
func Exists(path string) bool {
    _, err := os.Stat(path)
    if err != nil {
        return os.IsExist(err)  // ❌ 错误：应该是 !os.IsNotExist(err)
    }
    return true
}
```

**影响**：
- 对于不存在的路径，返回 `false`（恰好正确）
- 对于某些特殊情况（如权限错误），可能返回意外结果

**解决方案**：
```go
// 使用 Exist() 代替 Exists()
if osx.Exist(path) {
    // 安全的检查
}
```

#### 2. Copy() 不支持目录

```go
// ❌ 这将失败
err := osx.Copy("/tmp/dir", "/tmp/dir_copy")

// ✅ 目录复制需要递归实现
func copyDir(src, dst string) error {
    // 手动实现目录递归复制
}
```

#### 3. 符号链接处理

```go
// Copy() 会复制符号链接指向的内容，而不是链接本身
// 如果需要保留符号链接，需要特殊处理
```

### 使用建议

1. **优先使用 Exist() 而非 Exists()**
   - `Exist()` 实现正确
   - `Exists()` 已知有 Bug

2. **目录操作前先检查**
   ```go
   if osx.IsDir(path) {
       // 目录操作
   } else if osx.IsFile(path) {
       // 文件操作
   }
   ```

3. **大文件复制考虑进度显示**
   ```go
   // Copy() 没有进度回调
   // 对于大文件，考虑使用带进度显示的实现
   ```

4. **跨平台路径处理**
   ```go
   // 使用 filepath.Join() 而非字符串拼接
   path := filepath.Join(base, "subdir", "file.txt")
   ```

---

## 完整示例

### 示例 1：配置文件管理器

```go
package main

import (
    "fmt"
    "log"
    "os"

    "lazygophers/utils/osx"
)

type ConfigManager struct {
    configDir string
}

func NewConfigManager(dir string) *ConfigManager {
    return &ConfigManager{configDir: dir}
}

// 备份配置文件
func (cm *ConfigManager) BackupConfig(filename string) error {
    src := filepath.Join(cm.configDir, filename)
    dst := filepath.Join(cm.configDir, filename+".bak")

    // 检查源文件是否存在
    if !osx.Exist(src) {
        return fmt.Errorf("配置文件不存在: %s", src)
    }

    // 检查是否为文件
    if !osx.IsFile(src) {
        return fmt.Errorf("路径不是文件: %s", src)
    }

    // 复制文件
    if err := osx.Copy(src, dst); err != nil {
        return fmt.Errorf("备份失败: %w", err)
    }

    fmt.Printf("配置已备份: %s -> %s\n", src, dst)
    return nil
}

// 原子性更新配置
func (cm *ConfigManager) UpdateConfig(filename string, newContent []byte) error {
    src := filepath.Join(cm.configDir, filename)
    tmp := src + ".tmp"

    // 写入临时文件
    if err := os.WriteFile(tmp, newContent, 0644); err != nil {
        return fmt.Errorf("写入临时文件失败: %w", err)
    }

    // 原子性替换
    if err := osx.RenameForce(tmp, src); err != nil {
        os.Remove(tmp) // 清理
        return fmt.Errorf("更新配置失败: %w", err)
    }

    fmt.Printf("配置已更新: %s\n", src)
    return nil
}

func main() {
    cm := NewConfigManager("/etc/myapp")

    // 备份配置
    if err := cm.BackupConfig("config.json"); err != nil {
        log.Printf("备份失败: %v\n", err)
    }

    // 更新配置
    newConfig := []byte(`{"version":"2.0","debug":true}`)
    if err := cm.UpdateConfig("config.json", newConfig); err != nil {
        log.Printf("更新失败: %v\n", err)
    }
}
```

### 示例 2：文件系统工具

```go
package main

import (
    "fmt"
    "io/fs"
    "log"
    "os"
    "path/filepath"

    "lazygophers/utils/osx"
)

// FileTool 文件操作工具
type FileTool struct{}

// EnsureDir 确保目录存在
func (ft *FileTool) EnsureDir(path string) error {
    if osx.Exist(path) {
        if !osx.IsDir(path) {
            return fmt.Errorf("路径存在但不是目录: %s", path)
        }
        return nil // 目录已存在
    }

    if err := os.MkdirAll(path, 0755); err != nil {
        return fmt.Errorf("创建目录失败: %w", err)
    }

    fmt.Printf("目录已创建: %s\n", path)
    return nil
}

// SafeCopy 安全复制文件（带验证）
func (ft *FileTool) SafeCopy(src, dst string) error {
    // 检查源文件
    if !osx.Exist(src) {
        return fmt.Errorf("源文件不存在: %s", src)
    }

    if !osx.IsFile(src) {
        return fmt.Errorf("源路径不是文件: %s", src)
    }

    // 确保目标目录存在
    dstDir := filepath.Dir(dst)
    if err := ft.EnsureDir(dstDir); err != nil {
        return err
    }

    // 复制文件
    if err := osx.Copy(src, dst); err != nil {
        return fmt.Errorf("复制失败: %w", err)
    }

    // 验证复制结果
    if !osx.Exist(dst) || !osx.IsFile(dst) {
        return fmt.Errorf("复制验证失败")
    }

    fmt.Printf("文件已复制: %s -> %s\n", src, dst)
    return nil
}

// ReplaceFile 原子性替换文件
func (ft *FileTool) ReplaceFile(oldFile, newFile string) error {
    if !osx.Exist(newFile) {
        return fmt.Errorf("新文件不存在: %s", newFile)
    }

    // 备份旧文件
    if osx.Exist(oldFile) {
        backup := oldFile + ".bak"
        if err := osx.Copy(oldFile, backup); err != nil {
            return fmt.Errorf("备份失败: %w", err)
        }
        fmt.Printf("旧文件已备份: %s\n", backup)
    }

    // 原子性替换
    if err := osx.RenameForce(newFile, oldFile); err != nil {
        return fmt.Errorf("替换失败: %w", err)
    }

    fmt.Printf("文件已替换: %s\n", oldFile)
    return nil
}

func main() {
    ft := &FileTool{}

    // 创建目录
    if err := ft.EnsureDir("/tmp/myapp/data"); err != nil {
        log.Fatal(err)
    }

    // 安全复制
    if err := ft.SafeCopy("/tmp/source.txt", "/tmp/myapp/data/target.txt"); err != nil {
        log.Fatal(err)
    }

    // 原子性替换
    if err := ft.ReplaceFile("/tmp/config.txt", "/tmp/config.new"); err != nil {
        log.Fatal(err)
    }
}
```

### 示例 3：使用抽象文件系统进行测试

```go
package main

import (
    "fmt"
    "io/fs"
    "log"
    "testing/fstest"

    "lazygophers/utils/osx"
)

// AppConfig 应用配置（使用抽象文件系统）
type AppConfig struct {
    fsys fs.FS
}

func NewAppConfig(fsys fs.FS) *AppConfig {
    return &AppConfig{fsys: fsys}
}

// LoadConfig 加载配置文件
func (ac *AppConfig) LoadConfig(filename string) (string, error) {
    // 使用 FsHasFile 检查文件
    if !osx.FsHasFile(ac.fsys, filename) {
        return "", fmt.Errorf("配置文件不存在: %s", filename)
    }

    // 读取文件
    data, err := fs.ReadFile(ac.fsys, filename)
    if err != nil {
        return "", fmt.Errorf("读取配置失败: %w", err)
    }

    return string(data), nil
}

func main() {
    // 创建测试文件系统
    testFS := fstest.MapFS{
        "config.json":     &fstest.MapFile{Data: []byte(`{"debug":true}`)},
        "config.prod.json": &fstest.MapFile{Data: []byte(`{"debug":false}`)},
        "data/":          &fstest.MapFile{Mode: fs.ModeDir},
    }

    config := NewAppConfig(testFS)

    // 加载配置
    content, err := config.LoadConfig("config.json")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("配置内容: %s\n", content)

    // 检查文件存在性
    if osx.FsHasFile(testFS, "config.prod.json") {
        fmt.Println("生产环境配置存在")
    }
}
```

### 示例 4：路径类型检查工具

```go
package main

import (
    "fmt"
    "log"
    "path/filepath"

    "lazygophers/utils/osx"
)

// PathInfo 路径信息
type PathInfo struct {
    Path  string
    Exists bool
    IsDir  bool
    IsFile bool
}

// GetPathInfo 获取路径信息
func GetPathInfo(path string) PathInfo {
    info := PathInfo{
        Path:   path,
        Exists: osx.Exist(path),
    }

    if info.Exists {
        info.IsDir = osx.IsDir(path)
        info.IsFile = osx.IsFile(path)
    }

    return info
}

// DescribePath 描述路径
func DescribePath(path string) string {
    info := GetPathInfo(path)

    if !info.Exists {
        return fmt.Sprintf("%s: 不存在", path)
    }

    if info.IsDir {
        return fmt.Sprintf("%s: 目录", path)
    }

    if info.IsFile {
        return fmt.Sprintf("%s: 文件", path)
    }

    return fmt.Sprintf("%s: 未知类型", path)
}

func main() {
    paths := []string{
        "/tmp",
        "/etc/hosts",
        "/nonexistent",
        "/dev/null",
    }

    for _, path := range paths {
        info := DescribePath(path)
        fmt.Println(info)
    }

    // 使用 filepath.Join 构建路径
    configPath := filepath.Join("/etc", "myapp", "config.json")
    fmt.Printf("\n配置文件路径: %s\n", DescribePath(configPath))
}
```

---

## 总结

osx 模块提供了简洁高效的文件和路径操作工具：

### 核心优势

1. **零依赖**：仅使用标准库
2. **API 简洁**：函数命名清晰，易于理解
3. **类型安全**：布尔返回值简化错误处理
4. **测试友好**：支持抽象文件系统

### 常用操作

| 操作 | 推荐函数 | 说明 |
|------|---------|------|
| 检查存在 | `osx.Exist()` | 正确实现 |
| 判断目录 | `osx.IsDir()` | 快速判断 |
| 判断文件 | `osx.IsFile()` | 快速判断 |
| 文件复制 | `osx.Copy()` | 保留权限 |
| 强制重命名 | `osx.RenameForce()` | 原子操作 |
| 抽象文件系统 | `osx.FsHasFile()` | 测试友好 |

### 注意事项

- 避免使用 `Exists()`（有 Bug），使用 `Exist()`
- `Copy()` 不支持目录递归复制
- 符号链接会被复制为实际内容
- 跨平台路径使用 `filepath.Join()`

---

**相关模块**：
- [lrpc-anyx](../lrpc-anyx/) - 类型安全转换
- [lrpc-xtime](../lrpc-xtime/) - 时间处理
- [lazygophers/utils](https://github.com/lazygophers/utils) - 完整文档
