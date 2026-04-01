---
description: "C语言POSIX系统编程规范，涵盖文件描述符I/O、fork/exec进程管理、信号处理、socket网络编程、epoll/kqueue高性能I/O多路复用。适用于Linux/macOS系统编程和网络服务开发。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C POSIX API 规范

## 适用 Agents
- **dev** - 实现系统编程功能
- **debug** - 调试系统调用失败和文件描述符泄漏
- **perf** - epoll/kqueue 高性能 I/O

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(c:core) | C11/C17 标准 |
| 并发编程 | Skills(c:concurrency) | pthread、线程安全 |
| 错误处理 | Skills(c:error) | errno、perror、错误清理 |

## AI 理性化检查

| AI 理性化 | 实际检查 |
|----------|---------|
| "read/write 不需要循环" | 是否处理了 EINTR 和部分读写？ |
| "close 不会失败" | 是否检查了 close 返回值？ |
| "不需要处理 SIGCHLD" | 子进程退出是否会成为僵尸？ |
| "select 够用了" | 是否需要 epoll/kqueue 高并发？ |
| "信号处理器里可以 printf" | 是否只用了 async-signal-safe 函数？ |

## 文件描述符 I/O

```c
#include <fcntl.h>
#include <unistd.h>

int fd = open("data.txt", O_RDONLY);
if (fd == -1) { perror("open"); return -1; }

// 必须处理部分读写和 EINTR
ssize_t read_all(int fd, void* buf, size_t count) {
    size_t total = 0;
    while (total < count) {
        ssize_t n = read(fd, (char*)buf + total, count - total);
        if (n == -1) {
            if (errno == EINTR) continue;  // 信号中断，重试
            return -1;
        }
        if (n == 0) break;  // EOF
        total += (size_t)n;
    }
    return (ssize_t)total;
}

ssize_t write_all(int fd, const void* buf, size_t count) {
    size_t total = 0;
    while (total < count) {
        ssize_t n = write(fd, (const char*)buf + total, count - total);
        if (n == -1) {
            if (errno == EINTR) continue;
            return -1;
        }
        total += (size_t)n;
    }
    return (ssize_t)total;
}

// 关闭（必须检查返回值）
if (close(fd) == -1) { perror("close"); }
```

## 目录操作

```c
#include <dirent.h>
#include <sys/stat.h>

DIR* dir = opendir(".");
if (dir == NULL) { perror("opendir"); return -1; }

struct dirent* entry;
while ((entry = readdir(dir)) != NULL) {
    if (entry->d_name[0] == '.') continue;  // 跳过隐藏文件
    printf("%s\n", entry->d_name);
}
closedir(dir);

// 创建目录（处理 EEXIST）
if (mkdir("newdir", 0755) == -1 && errno != EEXIST) {
    perror("mkdir");
}
```

## 进程管理

```c
#include <sys/wait.h>
#include <unistd.h>

pid_t pid = fork();
if (pid == -1) {
    perror("fork");
    return -1;
}
if (pid == 0) {
    // 子进程
    execlp("ls", "ls", "-la", (char*)NULL);
    perror("execlp");  // exec 失败才会到这里
    _exit(EXIT_FAILURE);  // 子进程用 _exit 而非 exit
}

// 父进程等待
int status;
if (waitpid(pid, &status, 0) == -1) {
    perror("waitpid");
} else if (WIFEXITED(status)) {
    printf("Exit code: %d\n", WEXITSTATUS(status));
} else if (WIFSIGNALED(status)) {
    printf("Killed by signal: %d\n", WTERMSIG(status));
}
```

## 信号处理

```c
#include <signal.h>

// 使用 sigaction（不使用 signal()）
static volatile sig_atomic_t got_signal = 0;

void handler(int signo) {
    (void)signo;
    got_signal = 1;  // 仅设置 flag，async-signal-safe
}

struct sigaction sa = {
    .sa_handler = handler,
    .sa_flags = SA_RESTART,  // 自动重启被中断的系统调用
};
sigemptyset(&sa.sa_mask);
sigaction(SIGINT, &sa, NULL);
sigaction(SIGTERM, &sa, NULL);
```

## 网络编程（TCP）

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

// 服务端
int server_fd = socket(AF_INET, SOCK_STREAM, 0);
if (server_fd == -1) { perror("socket"); return -1; }

int opt = 1;
setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
    .sin_addr.s_addr = INADDR_ANY,
};

if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
    perror("bind"); close(server_fd); return -1;
}
if (listen(server_fd, SOMAXCONN) == -1) {
    perror("listen"); close(server_fd); return -1;
}

// 接受连接
int client_fd = accept(server_fd, NULL, NULL);
if (client_fd == -1) {
    if (errno == EINTR) { /* 重试 */ }
    perror("accept");
}
```

## I/O 多路复用（epoll/kqueue）

```c
// Linux epoll
#ifdef __linux__
#include <sys/epoll.h>

int epfd = epoll_create1(0);
struct epoll_event ev = { .events = EPOLLIN, .data.fd = server_fd };
epoll_ctl(epfd, EPOLL_CTL_ADD, server_fd, &ev);

struct epoll_event events[64];
int nfds = epoll_wait(epfd, events, 64, -1);
for (int i = 0; i < nfds; i++) {
    if (events[i].data.fd == server_fd) {
        // 新连接
    } else {
        // 数据就绪
    }
}
#endif

// macOS/BSD kqueue
#ifdef __APPLE__
#include <sys/event.h>

int kq = kqueue();
struct kevent change;
EV_SET(&change, server_fd, EVFILT_READ, EV_ADD, 0, 0, NULL);
kevent(kq, &change, 1, NULL, 0, NULL);

struct kevent events[64];
int n = kevent(kq, NULL, 0, events, 64, NULL);
#endif
```

## 检查清单

- [ ] 所有系统调用返回值已检查
- [ ] read/write 处理 EINTR 和部分读写
- [ ] 文件描述符正确关闭（无泄漏）
- [ ] fork 后子进程用 _exit 退出
- [ ] waitpid 回收子进程（无僵尸）
- [ ] 信号处理器仅用 async-signal-safe 函数
- [ ] 使用 sigaction 而非 signal()
- [ ] 套接字设置 SO_REUSEADDR
- [ ] 高并发使用 epoll(Linux)/kqueue(macOS)
