---
name: lrpc-runtime
description: lazygophers/utils runtime 模块完整指南 - 运行时环境检测、路径管理、Panic 处理、信号捕获和优雅退出
---

# lrpc-runtime

`runtime` 模块是 lazygophers/utils 库的核心基础模块，提供了运行时环境检测、文件路径管理、异常处理、信号捕获等基础设施功能。该模块是构建稳定可靠 Go 应用程序的基础。

---

## 模块概览

### 主要功能

- **系统平台检测**: Windows、Linux、macOS 平台识别
- **路径管理**: 可执行文件路径、工作目录、用户目录、应用配置/缓存目录
- **Panic 处理**: 捕获 panic、获取堆栈信息、自定义 panic 处理器
- **信号处理**: 捕获系统退出信号、优雅退出机制
- **进程控制**: 获取进程信息、发送退出信号

### 核心文件

```
runtime/
├── runtime.go              # 核心功能: panic处理、路径管理、堆栈追踪
├── exit.go                 # 退出信号处理
├── system_*.go             # 平台检测 (darwin, linux, windows)
├── exit_signal_*.go        # 平台特定的退出信号定义
└── *_test.go               # 完整的测试覆盖
```

---

## 平台检测

### IsWindows / IsDarwin / IsLinux

检测当前运行的操作系统平台。

```go
import "github.com/lazygophers/utils/runtime"

if runtime.IsWindows() {
    // Windows 特定逻辑
} else if runtime.IsDarwin() {
    // macOS 特定逻辑
} else if runtime.IsLinux() {
    // Linux 特定逻辑
}
```

### 实现原理

使用 Go 的 build tags 在编译时确定平台：

```go
// system_darwin.go
func IsWindows() bool { return false }
func IsDarwin() bool  { return true }
func IsLinux() bool   { return false }

// system_linux.go
func IsWindows() bool { return false }
func IsDarwin() bool  { return false }
func IsLinux() bool   { return true }

// system_windows.go
func IsWindows() bool { return true }
func IsDarwin() bool  { return false }
func IsLinux() bool   { return false }
```

**优点**: 编译期确定，零运行时开销
**注意**: 同一时间只有一个平台函数返回 `true`

---

## 路径管理

### 可执行文件路径

#### ExecFile() - 获取可执行文件的完整路径

```go
execPath := runtime.ExecFile()
// 示例输出: /usr/local/bin/myapp 或 C:\Program Files\MyApp\myapp.exe
```

#### ExecDir() - 获取可执行文件所在目录

```go
execDir := runtime.ExecDir()
// 示例输出: /usr/local/bin 或 C:\Program Files\MyApp
```

**用途**:
- 定位程序自身的资源文件
- 计算相对路径的基准目录
- 读取程序旁边的配置文件

### 当前工作目录

#### Pwd() - 获取当前工作目录

```go
cwd := runtime.Pwd()
// 示例输出: /Users/username/projects/myapp
```

**用途**:
- 获取程序启动时的工作目录
- 处理用户指定的相对路径
- 日志记录当前执行位置

### 用户目录

#### UserHomeDir() - 获取用户主目录

```go
homeDir := runtime.UserHomeDir()
// macOS/Linux: /Users/username 或 /home/username
// Windows: C:\Users\username
```

#### UserConfigDir() - 获取用户配置目录

```go
configDir := runtime.UserConfigDir()
// macOS:     /Users/username/Library/Application Support
// Linux:     /home/username/.config
// Windows:   C:\Users\username\AppData\Roaming
```

#### UserCacheDir() - 获取用户缓存目录

```go
cacheDir := runtime.UserCacheDir()
// macOS:     /Users/username/Library/Caches
// Linux:     /home/username/.cache
// Windows:   C:\Users\username\AppData\Local
```

**用途**:
- 存储用户级配置文件（非易失）
- 存储缓存数据（易失，可清理）
- 跨平台兼容的路径管理

### 应用特定目录

#### LazyConfigDir() - LazyGophers 应用配置目录

```go
configDir := runtime.LazyConfigDir()
// macOS:     ~/Library/Application Support/lazygophers
// Linux:     ~/.config/lazygophers
// Windows:   %APPDATA%\lazygophers
```

#### LazyCacheDir() - LazyGophers 应用缓存目录

```go
cacheDir := runtime.LazyCacheDir()
// macOS:     ~/Library/Caches/lazygophers
// Linux:     ~/.cache/lazygophers
// Windows:   %LOCALAPPDATA%\lazygophers
```

**用途**:
- 存储 lazygophers 生态应用的配置
- 统一的配置和缓存管理
- 符合 XDG Base Directory Specification (Linux)

### 路径管理最佳实践

```go
package main

import (
    "path/filepath"
    "github.com/lazygophers/utils/runtime"
)

func SetupAppDirectories() (configDir, dataDir, cacheDir string, err error) {
    // 配置目录 - 存储配置文件
    configDir = filepath.Join(runtime.LazyConfigDir(), "myapp")
    // 数据目录 - 存储持久化数据
    dataDir = filepath.Join(runtime.UserHomeDir(), ".myapp", "data")
    // 缓存目录 - 存储临时缓存
    cacheDir = filepath.Join(runtime.LazyCacheDir(), "myapp")

    // 创建必要的目录
    for _, dir := range []string{configDir, dataDir, cacheDir} {
        if err = os.MkdirAll(dir, 0755); err != nil {
            return "", "", "", err
        }
    }

    return configDir, dataDir, cacheDir, nil
}
```

---

## Panic 处理

### CachePanic() - 捕获 panic

捕获并处理 panic，打印堆栈信息到 stderr。

```go
func main() {
    defer runtime.CachePanic()

    // 你的程序逻辑
    // 如果发生 panic，会被捕获并打印堆栈
    doSomething()
}
```

**输出示例**:
```
PROCESS PANIC: err runtime error: index out of range [5] with length 3
dump stack (runtime error: index out of range [5] with length 3):
  goroutine 1 [running]:
  runtime/debug.Stack()
      /usr/local/go/src/runtime/debug/stack.go:24 +0x9f
  github.com/lazygophers/utils/runtime.CachePanic()
      /path/to/runtime/runtime.go:35 +0x85
  main.main()
      /path/to/main.go:15 +0x23
```

### CachePanicWithHandle() - 带 custom handler 的 panic 捕获

```go
func main() {
    defer runtime.CachePanicWithHandle(func(err interface{}) {
        // 自定义 panic 处理逻辑
        log.Errorf("Panic occurred: %v", err)

        // 发送告警
        sendAlert(err)

        // 保存堆栈到文件
        saveCrashReport(runtime.GetStack())
    })

    // 程序逻辑
}
```

### OnPanic() - 注册全局 panic 处理器

```go
func init() {
    // 注册多个 panic 处理器
    runtime.OnPanic(func(err interface{}) {
        log.Errorf("Handler 1: %v", err)
    })

    runtime.OnPanic(func(err interface{}) {
        sendAlert(err)
    })

    runtime.OnPanic(func(err interface{}) {
        cleanup()
    })
}

func main() {
    defer runtime.CachePanic()
    // 所有注册的处理器都会被调用
}
```

**注意**: 处理器按注册顺序调用，建议按以下顺序：
1. 日志记录
2. 数据清理
3. 告警通知

### GetStack() - 获取当前堆栈信息

```go
func SaveCrashReport() {
    stack := runtime.GetStack()
    err := os.WriteFile("crash.log", []byte(stack), 0644)
    if err != nil {
        log.Errorf("Failed to save crash report: %v", err)
    }
}
```

### PrintStack() - 打印堆栈到 stderr

```go
func DebugContext() {
    runtime.PrintStack()
    // 输出到 stderr，用于调试
}
```

**注意**: PrintStack() 使用最基础的系统调用（os.Stderr.WriteString），避免在处理 panic 时再次 panic（栈溢出）。

### Panic 处理最佳实践

```go
package main

import (
    "log"
    "os"
    "github.com/lazygophers/utils/runtime"
)

func main() {
    // 1. 注册全局 panic 处理器
    runtime.OnPanic(panicLogger)
    runtime.OnPanic(panicCleanup)
    runtime.OnPanic(panicAlert)

    // 2. 设置 defer 捕获 panic
    defer runtime.CachePanic()

    // 3. 程序主逻辑
    runApplication()
}

func panicLogger(err interface{}) {
    log.Printf("PANIC: %v", err)
    // 记录到日志文件
    f, _ := os.OpenFile("panic.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    defer f.Close()
    f.WriteString(runtime.GetStack())
}

func panicCleanup(err interface{}) {
    // 清理资源
    closeConnections()
    flushBuffers()
}

func panicAlert(err interface{}) {
    // 发送告警
    sendAlertToMonitoring("PANIC", err)
}
```

---

## 信号处理与优雅退出

### GetExitSign() - 获取退出信号通道

返回一个缓冲的信号通道，用于接收系统退出信号。

```go
sigCh := runtime.GetExitSign()
// sigCh 是一个 chan os.Signal，缓冲大小为 1
```

**监听的信号** (Linux/macOS):
- `SIGINT` (Ctrl+C)
- `SIGQUIT` (Ctrl+\)
- `SIGABRT` (abort)
- `SIGTERM` (termination)
- `SIGSTOP` (stop)
- `SIGTRAP` (trace trap)
- `SIGTSTP` (terminal stop)

**监听的信号** (Windows):
- `SIGINT`
- `SIGQUIT`
- `SIGABRT`
- `SIGTERM`
- `SIGTRAP`

### WaitExit() - 等待退出信号

阻塞直到收到退出信号。

```go
func main() {
    log.Println("Application started")

    // 启动服务
    go runServer()

    // 等待退出信号
    runtime.WaitExit()

    // 清理资源
    log.Println("Shutting down...")
    cleanup()

    log.Println("Application stopped")
}
```

**注意**: WaitExit() 会阻塞主 goroutine，通常作为 main 函数的最后一行。

### Exit() - 优雅退出

向当前进程发送中断信号，触发优雅退出。

```go
func HandleCriticalError() {
    if isCritical {
        log.Error("Critical error, exiting...")
        runtime.Exit()
        // 不会执行到这里，因为进程会收到 SIGINT
    }
}
```

**实现细节**:
```go
func Exit() {
    process, err := os.FindProcess(os.Getpid())
    if err != nil {
        log.Errorf("err:%v", err)
        os.Exit(0)
    } else {
        log.Infof("will stop process:%d", process.Pid)
        // 使用 SIGTERM 而不是 SIGKILL，允许进程清理
        err = process.Signal(os.Interrupt)
        if err != nil {
            log.Errorf("err:%v", err)
            os.Exit(0)
        }
    }
}
```

### 优雅退出最佳实践

```go
package main

import (
    "context"
    "log"
    "os"
    "os/signal"
    "sync"
    "time"
    "github.com/lazygophers/utils/runtime"
)

func main() {
    // 创建上下文用于取消操作
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // 启动后台服务
    var wg sync.WaitGroup
    wg.Add(1)
    go func() {
        defer wg.Done()
        runServer(ctx)
    }()

    // 监听退出信号
    go func() {
        runtime.WaitExit()
        log.Println("Received exit signal")

        // 取消上下文，通知所有 goroutine 退出
        cancel()
    }()

    // 等待所有服务清理完成
    wg.Wait()

    // 额外的清理工作
    cleanup()

    log.Println("Graceful shutdown completed")
}

func runServer(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            log.Println("Server shutting down...")
            // 清理服务器资源
            return
        default:
            // 正常业务逻辑
            time.Sleep(1 * time.Second)
        }
    }
}

func cleanup() {
    // 保存状态
    saveState()

    // 关闭连接
    closeConnections()

    // 刷新缓冲
    flushBuffers()
}
```

### 自定义信号处理

```go
func CustomSignalHandler() {
    sigCh := runtime.GetExitSign()

    for sig := range sigCh {
        log.Printf("Received signal: %v", sig)

        switch sig {
        case os.Interrupt:
            // Ctrl+C
            log.Println("Interrupt signal, shutting down...")
            handleShutdown()
            return

        case syscall.SIGTERM:
            // Termination signal
            log.Println("Termination signal, shutting down...")
            handleShutdown()
            return

        case syscall.SIGQUIT:
            // Quit signal (usually for debugging)
            log.Println("Quit signal, dumping state...")
            runtime.PrintStack()
            dumpState()

        default:
            log.Printf("Unhandled signal: %v", sig)
        }
    }
}
```

---

## 完整使用示例

### 示例 1: 基础应用框架

```go
package main

import (
    "log"
    "os"
    "path/filepath"
    "github.com/lazygophers/utils/runtime"
)

func main() {
    // 1. Panic 处理
    defer runtime.CachePanic()

    // 2. 设置日志
    setupLogging()

    // 3. 初始化目录
    initDirectories()

    // 4. 启动应用
    log.Printf("Application started (PID: %d)", os.Getpid())
    log.Printf("Exec: %s", runtime.ExecFile())
    log.Printf("Working: %s", runtime.Pwd())

    // 5. 运行主逻辑
    runApplication()
}

func setupLogging() {
    logDir := filepath.Join(runtime.LazyCacheDir(), "myapp", "logs")
    os.MkdirAll(logDir, 0755)

    logFile := filepath.Join(logDir, "app.log")
    f, err := os.OpenFile(logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        log.Fatal(err)
    }

    log.SetOutput(f)
}

func initDirectories() {
    // 配置目录
    configDir := filepath.Join(runtime.LazyConfigDir(), "myapp")
    os.MkdirAll(configDir, 0755)

    // 数据目录
    dataDir := filepath.Join(runtime.UserHomeDir(), ".myapp", "data")
    os.MkdirAll(dataDir, 0755)

    // 缓存目录
    cacheDir := filepath.Join(runtime.LazyCacheDir(), "myapp")
    os.MkdirAll(cacheDir, 0755)
}

func runApplication() {
    log.Println("Running application...")
    // 你的应用逻辑
}
```

### 示例 2: Web 服务器优雅退出

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "time"
    "github.com/lazygophers/utils/runtime"
)

func main() {
    // Panic 处理
    defer runtime.CachePanic()

    // 创建 HTTP 服务器
    server := &http.Server{
        Addr:    ":8080",
        Handler: newHandler(),
    }

    // 启动服务器
    go func() {
        log.Println("Server started on :8080")
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()

    // 监听退出信号
    runtime.WaitExit()

    // 优雅关闭
    log.Println("Shutting down server...")
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        log.Errorf("Server shutdown error: %v", err)
    }

    log.Println("Server stopped")
}

func newHandler() http.Handler {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Hello, World!"))
    })
    return mux
}
```

### 示例 3: 后台服务管理器

```go
package main

import (
    "log"
    "os"
    "sync"
    "time"
    "github.com/lazygophers/utils/runtime"
)

type ServiceManager struct {
    services []Service
    wg       sync.WaitGroup
    shutdown chan struct{}
}

type Service interface {
    Start() error
    Stop() error
    Name() string
}

func NewServiceManager() *ServiceManager {
    return &ServiceManager{
        shutdown: make(chan struct{}),
    }
}

func (sm *ServiceManager) Register(svc Service) {
    sm.services = append(sm.services, svc)
}

func (sm *ServiceManager) Start() error {
    log.Printf("Starting %d services...", len(sm.services))

    for _, svc := range sm.services {
        sm.wg.Add(1)
        go func(s Service) {
            defer sm.wg.Done()
            log.Printf("Service %s started", s.Name())

            if err := s.Start(); err != nil {
                log.Printf("Service %s error: %v", s.Name(), err)
            }

            log.Printf("Service %s stopped", s.Name())
        }(svc)
    }

    return nil
}

func (sm *ServiceManager) Stop() {
    log.Println("Stopping all services...")
    close(sm.shutdown)

    // 停止所有服务
    for _, svc := range sm.services {
        if err := svc.Stop(); err != nil {
            log.Printf("Error stopping %s: %v", svc.Name(), err)
        }
    }

    // 等待所有服务停止
    done := make(chan struct{})
    go func() {
        sm.wg.Wait()
        close(done)
    }()

    select {
    case <-done:
        log.Println("All services stopped")
    case <-time.After(30 * time.Second):
        log.Println("Timeout waiting for services to stop")
    }
}

func main() {
    defer runtime.CachePanic()

    // 创建服务管理器
    manager := NewServiceManager()

    // 注册服务
    manager.Register(&DatabaseService{})
    manager.Register(&CacheService{})
    manager.Register(&APIService{})

    // 启动服务
    if err := manager.Start(); err != nil {
        log.Fatal(err)
    }

    log.Printf("Application started (PID: %d)", os.Getpid())

    // 等待退出信号
    runtime.WaitExit()

    // 停止所有服务
    manager.Stop()

    log.Println("Application stopped")
}

// 示例服务实现
type DatabaseService struct{}

func (s *DatabaseService) Start() error { return nil }
func (s *DatabaseService) Stop() error  { return nil }
func (s *DatabaseService) Name() string  { return "database" }

type CacheService struct{}

func (s *CacheService) Start() error { return nil }
func (s *CacheService) Stop() error  { return nil }
func (s *CacheService) Name() string  { return "cache" }

type APIService struct{}

func (s *APIService) Start() error { return nil }
func (s *APIService) Stop() error  { return nil }
func (s *APIService) Name() string  { return "api" }
```

### 示例 4: 崩溃恢复和报告

```go
package main

import (
    "fmt"
    "os"
    "path/filepath"
    "runtime/debug"
    "time"
    "github.com/lazygophers/utils/runtime"
)

func main() {
    // 注册 panic 处理器
    runtime.OnPanic(saveCrashReport)
    runtime.OnPanic(sendCrashAlert)
    runtime.OnPanic(cleanupOnCrash)

    // 捕获 panic
    defer runtime.CachePanic()

    // 检查是否有未处理的崩溃
    checkPreviousCrash()

    // 删除旧的崩溃报告
    defer cleanupOldCrashReports()

    // 运行应用
    runApplication()
}

func saveCrashReport(err interface{}) {
    timestamp := time.Now().Format("20060102-150405")
    crashFile := filepath.Join(runtime.LazyCacheDir(), "myapp", "crashes", timestamp+".log")

    os.MkdirAll(filepath.Dir(crashFile), 0755)

    report := fmt.Sprintf("Crash Report - %s\n", timestamp)
    report += fmt.Sprintf("Error: %v\n", err)
    report += fmt.Sprintf("PID: %d\n", os.Getpid())
    report += fmt.Sprintf("Executable: %s\n", runtime.ExecFile())
    report += fmt.Sprintf("Working Dir: %s\n", runtime.Pwd())
    report += "\n=== Stack Trace ===\n"
    report += runtime.GetStack()
    report += "\n=== Build Info ===\n"
    info, ok := debug.ReadBuildInfo()
    if ok {
        report += fmt.Sprintf("Go Version: %s\n", info.GoVersion)
        report += fmt.Sprintf("Main Path: %s\n", info.Path)
    }

    if err := os.WriteFile(crashFile, []byte(report), 0644); err != nil {
        fmt.Printf("Failed to save crash report: %v\n", err)
    } else {
        fmt.Printf("Crash report saved to: %s\n", crashFile)
    }
}

func sendCrashAlert(err interface{}) {
    // 发送告警到监控系统
    alert := map[string]interface{}{
        "type":      "panic",
        "error":     fmt.Sprintf("%v", err),
        "pid":       os.Getpid(),
        "timestamp": time.Now().Unix(),
        "stack":     runtime.GetStack(),
    }

    // 发送到告警系统 (伪代码)
    // alerting.Send(alert)

    fmt.Printf("Crash alert sent: %v\n", err)
}

func cleanupOnCrash(err interface{}) {
    fmt.Println("Cleaning up after crash...")
    // 清理资源
    // 关闭连接
    // 刷新缓冲
}

func checkPreviousCrash() {
    crashDir := filepath.Join(runtime.LazyCacheDir(), "myapp", "crashes")
    files, err := os.ReadDir(crashDir)
    if err != nil {
        return
    }

    if len(files) > 0 {
        fmt.Printf("Warning: %d previous crash(es) detected\n", len(files))
        fmt.Println("Please check the crash reports in:", crashDir)
    }
}

func cleanupOldCrashReports() {
    crashDir := filepath.Join(runtime.LazyCacheDir(), "myapp", "crashes")
    files, err := os.ReadDir(crashDir)
    if err != nil {
        return
    }

    // 删除 7 天前的崩溃报告
    cutoff := time.Now().AddDate(0, 0, -7)
    for _, file := range files {
        info, err := file.Info()
        if err != nil {
            continue
        }

        if info.ModTime().Before(cutoff) {
            path := filepath.Join(crashDir, file.Name())
            os.Remove(path)
            fmt.Printf("Deleted old crash report: %s\n", file.Name())
        }
    }
}

func runApplication() {
    fmt.Println("Application running...")
    time.Sleep(1 * time.Second)

    // 模拟 panic
    panic("something went wrong!")
}
```

---

## 平台特定信号说明

### Linux 信号支持

标准 Linux (x86_64, amd64):
```go
syscall.SIGINT   // Ctrl+C
syscall.SIGQUIT  // Ctrl+\
syscall.SIGABRT  // abort()
syscall.SIGKILL  // kill -9
syscall.SIGTERM  // kill (default)
syscall.SIGSTOP  // pause
syscall.SIGTRAP  // trace trap
syscall.SIGTSTP  // Ctrl+Z
```

Linux ARM64:
```go
// 与标准 Linux 相同
```

Linux MIPS/MIPS64/MIPSLE/MIPS64LE:
```go
// 特殊架构的信号定义略有不同
// 参见 exit_signal_linux_mips*.go
```

### macOS (Darwin) 信号支持

```go
syscall.SIGINT   // Ctrl+C
syscall.SIGQUIT  // Ctrl+\
syscall.SIGABRT  // abort()
syscall.SIGKILL  // kill -9
syscall.SIGTERM  // kill (default)
syscall.SIGSTOP  // pause
syscall.SIGTRAP  // trace trap
syscall.SIGTSTP  // Ctrl+Z
```

### Windows 信号支持

Windows 支持的信号较少:
```go
syscall.SIGINT   // Ctrl+C
syscall.SIGQUIT  // (limited support)
syscall.SIGABRT  // abort()
syscall.SIGKILL  // (limited support)
syscall.SIGTERM  // (limited support)
syscall.SIGTRAP  // (limited support)
```

**注意**: Windows 的信号处理能力有限，建议使用 Windows 特定的退出机制（如服务控制管理器）。

### 其他 Unix 系统

- **FreeBSD**: `exit_signal_freebsd.go`
- **OpenBSD**: `exit_signal_openbsd.go`
- **NetBSD**: `exit_signal_netbsd.go`
- **DragonFly**: `exit_signal_dragonfly.go`
- **Solaris**: `exit_signal_solaris.go`
- **Plan 9**: `exit_signal_plan9.go`

---

## 测试覆盖

runtime 模块拥有完整的测试覆盖，包括：

- 单元测试 (`runtime_test.go`, `exit_test.go`, `system_test.go`)
- 覆盖率测试 (`runtime_coverage_test.go`, `exit_coverage_test.go`)
- 边界情况测试 (`runtime_edge_test.go`)
- Panic 场景测试 (`panic_coverage_test.go`)
- 错误分支测试 (`error_branches_test.go`)

运行测试:
```bash
go test -v github.com/lazygophers/utils/runtime
go test -cover github.com/lazygophers/utils/runtime
go test -race github.com/lazygophers/utils/runtime
```

---

## 性能考虑

### 零运行时开销的平台检测

使用 build tags 的平台检测在编译期确定，运行时零开销:

```go
if runtime.IsLinux() {
    // 这个分支在编译时就确定了
    // 运行时没有任何 if 判断开销
}
```

### Panic 处理性能

- `CachePanic()` 只在 panic 时执行，正常路径无开销
- 使用 `defer` 的性能影响极小
- `GetStack()` 和 `PrintStack()` 使用缓冲区减少内存分配

### 路径缓存

虽然 runtime 模块本身不缓存路径，但调用方可以缓存:

```go
var (
    cachedExecDir     string
    cachedExecDirOnce sync.Once
)

func GetExecDir() string {
    cachedExecDirOnce.Do(func() {
        cachedExecDir = runtime.ExecDir()
    })
    return cachedExecDir
}
```

---

## 最佳实践总结

### 1. 总是使用 defer CachePanic()

```go
func main() {
    defer runtime.CachePanic()  // ✅ 推荐
    // 程序逻辑
}
```

### 2. 使用 WaitExit() 而不是直接监听信号

```go
// ❌ 不推荐
sigCh := make(chan os.Signal, 1)
signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM, ...)
<-sigCh

// ✅ 推荐
runtime.WaitExit()
```

### 3. 使用 LazyConfigDir/LazyCacheDir 存储应用数据

```go
// ❌ 不推荐
configPath := "/usr/local/myapp/config.json"

// ✅ 推荐
configPath := filepath.Join(runtime.LazyConfigDir(), "myapp", "config.json")
```

### 4. 按顺序注册 panic 处理器

```go
// 1. 日志记录 (最先)
runtime.OnPanic(logPanic)

// 2. 数据清理
runtime.OnPanic(cleanup)

// 3. 告警通知 (最后)
runtime.OnPanic(sendAlert)
```

### 5. 优雅退出要有超时

```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

if err := server.Shutdown(ctx); err != nil {
    log.Errorf("Shutdown timeout: %v", err)
}
```

---

## 常见问题

### Q: 为什么不使用标准库的 runtime 包?

A: lazygophers/utils/runtime 提供了更高级的功能:
- 统一的路径管理（跨平台兼容）
- Panic 捕获和自定义处理
- 优雅退出机制
- 信号处理封装

标准库 `runtime` 包主要提供底层运行时信息，而 lazygophers/utils/runtime 提供应用级的基础设施。

### Q: CachePanic() 会恢复 panic 吗?

A: **不会**。`CachePanic()` 只捕获 panic、打印堆栈、调用处理器，然后程序会继续 panic。

```go
defer runtime.CachePanic()
// panic 后，程序仍然会退出
```

如果想**恢复** panic（继续执行），需要使用 `recover()`:

```go
defer func() {
    if err := recover(); err != nil {
        runtime.CachePanicWithHandle(func(err interface{}) {
            log.Printf("Recovered from panic: %v", err)
        })
    }
}()
```

### Q: WaitExit() 会阻塞多久?

A: **直到收到退出信号为止**。通常放在 `main()` 函数最后:

```go
func main() {
    // 启动服务
    go runServer()

    // 阻塞直到收到 SIGINT/SIGTERM
    runtime.WaitExit()

    // 清理资源
    cleanup()
}
```

### Q: 如何在 Windows 上使用信号处理?

A: Windows 的信号支持有限，建议:
1. 使用 Windows 服务机制
2. 使用控制台事件处理
3. 或者使用跨平台的 `WaitExit()`

### Q: 路径函数会创建目录吗?

A: **不会**。路径函数只返回路径字符串，不会创建目录:

```go
configDir := runtime.LazyConfigDir()  // 只返回路径
os.MkdirAll(configDir, 0755)          // 需要手动创建
```

---

## 依赖关系

runtime 模块依赖:
- `github.com/lazygophers/log` - 日志库
- `github.com/lazygophers/utils/app` - 应用组织信息

被依赖:
- 几乎所有 lazygophers/utils 模块
- lazygophers 生态的所有应用

---

## 参考资料

- [Go runtime package](https://pkg.go.dev/runtime) - Go 标准库 runtime 包
- [Go signal package](https://pkg.go.dev/os/signal) - Go 标准库 signal 包
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) - Linux 目录规范
- [lazygophers/utils GitHub](https://github.com/lazygophers/utils) - 完整源代码

---

## 版本要求

- Go >= 1.25.0
- 适用于所有主流平台 (Linux, macOS, Windows, BSD variants)

---

**最后更新**: 2026-01-28
**维护者**: lazygophers
