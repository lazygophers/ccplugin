---
name: c-posix
description: |
  C POSIX systems programming conventions: file descriptor I/O with EINTR + short-read
  loops, directory traversal, fork/exec/waitpid, sigaction-based signal handling,
  BSD/POSIX sockets, and high-throughput I/O multiplexing (epoll on Linux, kqueue on
  macOS/BSD, poll as portable fallback). Use when writing Linux/macOS system tools,
  network daemons, or wrapping syscalls. Triggers on "POSIX", "fork exec", "waitpid",
  "sigaction", "epoll", "kqueue", "socket", "EINTR", "SO_REUSEADDR", "non-blocking IO".
---

# C POSIX 系统编程规范

## 强制约定

1. 所有系统调用返回值必须检查；`-1 + errno` 为唯一可靠错误信号。
2. `read / write` 处理 `EINTR` 与短读短写（封装 `read_all / write_all`）。
3. `close` 也要检查返回值（特别是写文件后）。
4. `fork` 子进程退出用 `_exit`，不要走 `atexit / stdio flush`。
5. `waitpid` 回收所有子进程，避免僵尸；或显式 `SA_NOCLDWAIT`。
6. 信号注册一律 `sigaction` + `sigemptyset`；不用 `signal()`（语义跨平台不一致）。
7. 服务端 socket 设 `SO_REUSEADDR`；现代应用同时考虑 `SO_REUSEPORT`。
8. 高并发场景使用 `epoll`(Linux) / `kqueue`(macOS/BSD)，跨平台兜底用 `poll`。

## fd I/O 封装

```c
ssize_t read_all(int fd, void *buf, size_t n) {
    size_t tot = 0;
    while (tot < n) {
        ssize_t r = read(fd, (char *)buf + tot, n - tot);
        if (r < 0) { if (errno == EINTR) continue; return -1; }
        if (r == 0) break;          // EOF
        tot += (size_t)r;
    }
    return (ssize_t)tot;
}

ssize_t write_all(int fd, const void *buf, size_t n) {
    size_t tot = 0;
    while (tot < n) {
        ssize_t w = write(fd, (const char *)buf + tot, n - tot);
        if (w < 0) { if (errno == EINTR) continue; return -1; }
        tot += (size_t)w;
    }
    return (ssize_t)tot;
}
```

设置 `O_CLOEXEC`（`open(... O_CLOEXEC)`、`accept4`、`pipe2`）防止 fd 在 `exec` 后泄漏。

## fork / exec / waitpid

```c
pid_t pid = fork();
if (pid < 0) { perror("fork"); return -1; }
if (pid == 0) {
    execvp(argv[0], argv);
    perror("execvp");
    _exit(127);
}
int status;
while (waitpid(pid, &status, 0) < 0)
    if (errno != EINTR) { perror("waitpid"); break; }
if (WIFEXITED(status))   /* WEXITSTATUS(status) */;
if (WIFSIGNALED(status)) /* WTERMSIG(status) */;
```

## 信号处理

```c
static volatile sig_atomic_t stop = 0;
static void on_term(int sig) { (void)sig; stop = 1; }

struct sigaction sa = { .sa_handler = on_term, .sa_flags = SA_RESTART };
sigemptyset(&sa.sa_mask);
sigaction(SIGINT,  &sa, NULL);
sigaction(SIGTERM, &sa, NULL);
```

避免 `SA_RESTART` 与需要超时退出的循环混用——按需选择不带 `SA_RESTART` 并显式处理 `EINTR`。

## 网络（TCP）

```c
int srv = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
int one = 1;
setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
#ifdef SO_REUSEPORT
setsockopt(srv, SOL_SOCKET, SO_REUSEPORT, &one, sizeof one);
#endif

struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port   = htons(8080),
    .sin_addr.s_addr = htonl(INADDR_ANY),
};
bind(srv, (struct sockaddr *)&addr, sizeof addr);
listen(srv, SOMAXCONN);
```

非阻塞：`fcntl(fd, F_SETFL, O_NONBLOCK)`，或 `accept4(srv, ..., SOCK_NONBLOCK|SOCK_CLOEXEC)`。

## I/O 多路复用

### Linux epoll

```c
int ep = epoll_create1(EPOLL_CLOEXEC);
struct epoll_event ev = { .events = EPOLLIN | EPOLLET, .data.fd = srv };
epoll_ctl(ep, EPOLL_CTL_ADD, srv, &ev);

struct epoll_event evs[64];
int n = epoll_wait(ep, evs, 64, -1);
for (int i = 0; i < n; i++) { /* ... */ }
```

### macOS / BSD kqueue

```c
int kq = kqueue();
struct kevent ch;
EV_SET(&ch, srv, EVFILT_READ, EV_ADD, 0, 0, NULL);
kevent(kq, &ch, 1, NULL, 0, NULL);
struct kevent evs[64];
int n = kevent(kq, NULL, 0, evs, 64, NULL);
```

### 可移植兜底 `poll` / `ppoll`

中等并发（<1000 fd）跨平台使用 `poll`；需要原子修改信号掩码用 `ppoll` / `pselect`。

## 文件系统

- `mkdir` 处理 `EEXIST`。
- `readdir` 不需要 `readdir_r`（已废弃，POSIX.1-2008 起 `readdir` 在不同 DIR 上线程安全）。
- 大文件读写用 `pread / pwrite` 避免显式 `lseek`。
- `mmap` 适合大文件随机访问；记得 `madvise(MADV_RANDOM/SEQUENTIAL)`。

## 进程间通信

| 机制 | 适用 |
|------|------|
| pipe / pipe2 | 父子 / 兄弟 |
| socketpair | 双向，跨 exec |
| POSIX shm + sem | 大数据共享 |
| Unix domain socket + SCM_RIGHTS | 跨进程传 fd |

## 检查清单

- [ ] 所有系统调用返回值已检查
- [ ] `read/write` 处理 `EINTR` + 短读写
- [ ] `O_CLOEXEC` / `SOCK_CLOEXEC` 设置
- [ ] 子进程用 `_exit`，父进程 `waitpid` 回收
- [ ] 信号一律 `sigaction`
- [ ] 服务端设 `SO_REUSEADDR`（可选 `SO_REUSEPORT`）
- [ ] 高并发用 epoll / kqueue，可移植用 poll
- [ ] 无 fd 泄漏（ASan + LeakSanitizer + `lsof` 自检）

## 权威参考

- POSIX.1-2017 / IEEE Std 1003.1 — <https://pubs.opengroup.org/onlinepubs/9699919799/>
- Linux man-pages — <https://man7.org/linux/man-pages/>
- epoll(7) — <https://man7.org/linux/man-pages/man7/epoll.7.html>
- kqueue(2) (FreeBSD) — <https://man.freebsd.org/cgi/man.cgi?kqueue>
- W. R. Stevens, *Advanced Programming in the UNIX Environment* (APUE)
