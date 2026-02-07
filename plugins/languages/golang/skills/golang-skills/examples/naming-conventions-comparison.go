// ============================================================================
// GOOD EXAMPLE: 命名规范
// ============================================================================
// 说明：符合 golang-skills 命名规范
// 1. 导出类型使用 PascalCase
// 2. 私有函数使用 camelCase
// 3. 接收者使用单字母
// 4. 常量使用 UPPER_CASE

package main

import "time"

const (
    MaxRetries      = 3
    DefaultTimeout  = 30 * time.Second
)

type User struct {
    Id        int64
    Email     string
    IsActive  bool
    Status    int32
    CreatedAt time.Time
    UpdatedAt time.Time
}

func (u *User) IsAdmin() bool {
    return u.Status == 1
}

func GetUserById(id int64) (*User, error) {
    return &User{Id: id}, nil
}

func ListUsers() ([]*User, error) {
    return []*User{}, nil
}

func (u *User) validateEmail() error {
    return nil
}

// ============================================================================
// BAD EXAMPLE: 命名规范
// ============================================================================
// 说明：不符合 golang-skills 命名规范
// 1. 混合大小写规则
// 2. 无意义的短名
// 3. 过长的变量名
// 4. 缩写不清楚

package main

import "time"

const (
    maxRetries = 3
    Default   = 30 * time.Second
)

type user struct {
    UserID    int64
    user_email string
    isActive  bool
    status    string
    Created   time.Time
}

func (u *user) isAdmin() bool {
    return u.status == "active"
}

func Get(id int64) (*user, error) {
    return &user{UserID: id}, nil
}

func GetAllUsers() ([]*user, error) {
    return []*user{}, nil
}

func (u *user) validate() error {
    return nil
}
