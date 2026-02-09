# 系统编程

## POSIX 文件操作

### 文件描述符

```c
#include <fcntl.h>
#include <unistd.h>

// ✅ 打开文件
int fd = open("data.txt", O_RDONLY);
if (fd == -1) {
    perror("open");
    return -1;
}

// ✅ 创建文件（权限 0644）
int fd = open("new.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
if (fd == -1) {
    perror("open");
    return -1;
}

// ✅ 读写
ssize_t bytes_read = read(fd, buffer, sizeof(buffer));
if (bytes_read == -1) {
    perror("read");
}

ssize_t bytes_written = write(fd, data, size);
if (bytes_written == -1) {
    perror("write");
}

// ✅ 关闭
if (close(fd) == -1) {
    perror("close");
}

// ✅ 定位
off_t offset = lseek(fd, 0, SEEK_SET);  // 文件开头
offset = lseek(fd, 0, SEEK_END);        // 文件末尾
offset = lseek(fd, 0, SEEK_CUR);        // 当前位置
```

### 目录操作

```c
#include <dirent.h>

// ✅ 遍历目录
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

// ✅ 创建目录
#include <sys/stat.h>
#include <sys/types.h>

if (mkdir("newdir", 0755) == -1) {
    if (errno != EEXIST) {
        perror("mkdir");
    }
}
```

## 进程管理

### fork 和 exec

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
    // 子进程
    execlp("ls", "ls", "-l", NULL);
    perror("execlp");  // 只有 exec 失败才执行
    exit(EXIT_FAILURE);
}

// 父进程
int status;
if (waitpid(pid, &status, 0) == -1) {
    perror("waitpid");
    return -1;
}

if (WIFEXITED(status)) {
    printf("Child exited with status: %d\n", WEXITSTATUS(status));
}
```

### 管道

```c
int pipefd[2];
if (pipe(pipefd) == -1) {
    perror("pipe");
    return -1;
}

pid_t pid = fork();
if (pid == -1) {
    perror("fork");
    return -1;
}

if (pid == 0) {
    // 子进程：关闭写端，从读端读取
    close(pipefd[1]);

    char buffer[256];
    ssize_t bytes;
    while ((bytes = read(pipefd[0], buffer, sizeof(buffer))) > 0) {
        write(STDOUT_FILENO, buffer, bytes);
    }

    close(pipefd[0]);
    exit(EXIT_SUCCESS);
}

// 父进程：关闭读端，向写端写入
close(pipefd[0]);
write(pipefd[1], "Hello from parent", 18);
close(pipefd[1]);

wait(NULL);
```

## 线程

### pthread 创建

```c
#include <pthread.h>

void* thread_func(void* arg) {
    int value = *(int*)arg;
    printf("Thread received: %d\n", value);
    return NULL;
}

int main(void) {
    pthread_t thread;
    int arg = 42;

    if (pthread_create(&thread, NULL, thread_func, &arg) != 0) {
        perror("pthread_create");
        return EXIT_FAILURE;
    }

    // 等待线程完成
    if (pthread_join(thread, NULL) != 0) {
        perror("pthread_join");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
```

### 互斥锁

```c
#include <pthread.h>

pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
int shared_counter = 0;

void* increment(void* arg) {
    for (int i = 0; i < 1000; i++) {
        pthread_mutex_lock(&mutex);
        shared_counter++;
        pthread_mutex_unlock(&mutex);
    }
    return NULL;
}

// 记得销毁
pthread_mutex_destroy(&mutex);
```

## 网络编程

### TCP 客户端

```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

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

// 发送/接收
const char* message = "Hello, Server!";
send(sockfd, message, strlen(message), 0);

char buffer[256];
ssize_t bytes = recv(sockfd, buffer, sizeof(buffer) - 1, 0);
if (bytes > 0) {
    buffer[bytes] = '\0';
    printf("Received: %s\n", buffer);
}

close(sockfd);
```

---

**最后更新**：2026-02-09
