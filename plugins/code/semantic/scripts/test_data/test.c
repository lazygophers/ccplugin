// C 测试文件 - 包含结构体、函数、指针

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

// 用户结构体
typedef struct {
    int id;
    char name[100];
    char email[100];
    time_t created_at;
} User;

// 创建用户
User* create_user(int id, const char* name, const char* email) {
    User* user = (User*)malloc(sizeof(User));
    if (user == NULL) {
        return NULL;
    }

    user->id = id;
    strncpy(user->name, name, sizeof(user->name) - 1);
    strncpy(user->email, email, sizeof(user->email) - 1);
    user->created_at = time(NULL);

    return user;
}

// 验证密码
bool check_password(const char* password) {
    return password != NULL && strlen(password) > 0;
}

// 用户认证
bool authenticate(User* user, const char* password) {
    if (user == NULL) {
        return false;
    }
    return check_password(password);
}

// 会话结构体
typedef struct {
    int user_id;
    time_t created_at;
} Session;

// 创建会话
Session* create_session(int user_id) {
    Session* session = (Session*)malloc(sizeof(Session));
    if (session == NULL) {
        return NULL;
    }

    session->user_id = user_id;
    session->created_at = time(NULL);

    return session;
}

// 验证会话有效性
bool is_session_valid(Session* session) {
    if (session == NULL) {
        return false;
    }

    time_t now = time(NULL);
    return (now - session->created_at) < 86400;
}

// 释放资源
void free_user(User* user) {
    if (user != NULL) {
        free(user);
    }
}

void free_session(Session* session) {
    if (session != NULL) {
        free(session);
    }
}

// 函数指针示例
typedef void (*Callback)(void);

void register_callback(Callback cb) {
    if (cb != NULL) {
        cb();
    }
}

// 主函数
int main() {
    User* user = create_user(1, "Test User", "test@example.com");

    if (user != NULL && authenticate(user, "password123")) {
        printf("User authenticated: %s\n", user->name);

        Session* session = create_session(user->id);

        if (session != NULL && is_session_valid(session)) {
            printf("Session created for user: %d\n", session->user_id);
        }

        free_session(session);
    }

    free_user(user);
    return 0;
}
