# POSIX API 参考

## 文件系统

### stat：文件信息

```c
#include <sys/stat.h>

struct stat st;
if (stat("file.txt", &st) == -1) {
    perror("stat");
    return -1;
}

printf("File size: %ld bytes\n", st.st_size);
printf("Permissions: %o\n", st.st_mode & 0777);
printf("Is directory: %s\n", S_ISDIR(st.st_mode) ? "yes" : "no");
printf("Is regular file: %s\n", S_ISREG(st.st_mode) ? "yes" : "no");

// lstat 不跟随符号链接
struct stat lst;
if (lstat("symlink", &lst) == 0) {
    if (S_ISLNK(lst.st_mode)) {
        printf("Is symbolic link\n");
    }
}
```

## 进程控制

### getpid/getppid

```c
#include <unistd.h>
#include <sys/types.h>

pid_t pid = getpid();
pid_t ppid = getppid();

printf("PID: %d, PPID: %d\n", pid, ppid);
```

### 进程创建

```c
#include <unistd.h>
#include <sys/wait.h>

pid_t pid = fork();

switch (pid) {
    case -1:
        perror("fork");
        break;
    case 0:
        // 子进程
        printf("Child PID: %d\n", getpid());
        _exit(EXIT_SUCCESS);
    default:
        // 父进程
        printf("Parent PID: %d, Child PID: %d\n", getpid(), pid);
        int status;
        waitpid(pid, &status, 0);
        break;
}
```

## 信号

### 信号处理

```c
#include <signal.h>

void sigint_handler(int signo) {
    // 不要在信号处理器中使用不安全的函数
    _exit(EXIT_SUCCESS);
}

int main(void) {
    // 设置信号处理器
    signal(SIGINT, sigint_handler);

    // 或者使用 sigaction（推荐）
    struct sigaction sa = {
        .sa_handler = sigint_handler,
        .sa_flags = SA_RESTART
    };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);

    // 等待信号
    pause();

    return 0;
}
```

## 线程

### pthread 条件变量

```c
#include <pthread.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
int ready = 0;

void* waiter(void* arg) {
    pthread_mutex_lock(&mutex);
    while (!ready) {
        pthread_cond_wait(&cond, &mutex);
    }
    pthread_mutex_unlock(&mutex);
    return NULL;
}

void* signaler(void* arg) {
    pthread_mutex_lock(&mutex);
    ready = 1;
    pthread_cond_signal(&cond);
    pthread_mutex_unlock(&mutex);
    return NULL;
}
```

## 网络套接字

### UDP 服务器

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
if (sockfd == -1) {
    perror("socket");
    return -1;
}

struct sockaddr_in addr = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
    .sin_addr = { .s_addr = INADDR_ANY }
};

if (bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) == -1) {
    perror("bind");
    close(sockfd);
    return -1;
}

char buffer[1024];
struct sockaddr_in client;
socklen_t client_len = sizeof(client);

ssize_t bytes = recvfrom(sockfd, buffer, sizeof(buffer) - 1, 0,
                        (struct sockaddr*)&client, &client_len);
if (bytes > 0) {
    buffer[bytes] = '\0';
    printf("Received from %s:%d - %s\n",
           inet_ntoa(client.sin_addr),
           ntohs(client.sin_port),
           buffer);
}

close(sockfd);
```

---

**最后更新**：2026-02-09
