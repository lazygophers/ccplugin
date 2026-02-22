---
name: posix
description: C POSIX API 规范：文件系统、进程管理、信号处理、网络编程。使用 POSIX API 时必须加载。
---

# C POSIX API 规范

## 相关 Skills

| 场景     | Skill               | 说明                   |
| -------- | ------------------- | ---------------------- |
| 核心规范 | Skills(core)        | C11/C17 标准、强制约定 |
| 并发编程 | Skills(concurrency) | pthread、线程安全      |
| 错误处理 | Skills(error)       | errno、perror          |

## 文件描述符

```c
#include <fcntl.h>
#include <unistd.h>

int fd = open("data.txt", O_RDONLY);
if (fd == -1) {
    perror("open");
    return -1;
}

int fd = open("new.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
if (fd == -1) {
    perror("open");
    return -1;
}

ssize_t bytes_read = read(fd, buffer, sizeof(buffer));
if (bytes_read == -1) {
    perror("read");
}

ssize_t bytes_written = write(fd, data, size);
if (bytes_written == -1) {
    perror("write");
}

if (close(fd) == -1) {
    perror("close");
}

off_t offset = lseek(fd, 0, SEEK_SET);
offset = lseek(fd, 0, SEEK_END);
offset = lseek(fd, 0, SEEK_CUR);
```

## 目录操作

```c
#include <dirent.h>
#include <sys/stat.h>
#include <sys/types.h>

DIR* dir = opendir(".");
if (dir == NULL) {
    perror("opendir");
    return -1;
}

struct dirent* entry;
while ((entry = readdir(dir)) != NULL) {
    printf("%s\n", entry->d_name);
}

if (closedir(dir) == -1) {
    perror("closedir");
}

if (mkdir("newdir", 0755) == -1) {
    if (errno != EEXIST) {
        perror("mkdir");
    }
}
```

## 进程管理

```c
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

pid_t pid = fork();
if (pid == -1) {
    perror("fork");
    return -1;
}

if (pid == 0) {
    execlp("ls", "ls", "-l", NULL);
    perror("execlp");
    exit(EXIT_FAILURE);
}

int status;
if (waitpid(pid, &status, 0) == -1) {
    perror("waitpid");
    return -1;
}

if (WIFEXITED(status)) {
    printf("Child exited with status: %d\n", WEXITSTATUS(status));
}
```

## 信号处理

```c
#include <signal.h>

void sigint_handler(int signo) {
    _exit(EXIT_SUCCESS);
}

int main(void) {
    struct sigaction sa = {
        .sa_handler = sigint_handler,
        .sa_flags = SA_RESTART
    };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);

    pause();
    return 0;
}
```

## 网络编程

### TCP 客户端

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int sockfd = socket(AF_INET, SOCK_STREAM, 0);
if (sockfd == -1) {
    perror("socket");
    return -1;
}

struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
    .sin_addr = { .s_addr = INADDR_ANY }
};

if (connect(sockfd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
    perror("connect");
    close(sockfd);
    return -1;
}

send(sockfd, message, strlen(message), 0);

char buffer[256];
ssize_t bytes = recv(sockfd, buffer, sizeof(buffer) - 1, 0);
if (bytes > 0) {
    buffer[bytes] = '\0';
}

close(sockfd);
```

## 检查清单

- [ ] 所有系统调用返回值已检查
- [ ] 文件描述符正确关闭
- [ ] 进程正确等待
- [ ] 信号处理器使用安全函数
- [ ] 套接字正确关闭
