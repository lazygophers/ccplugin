// ============================================================================
// GOOD EXAMPLE: 函数式编程
// ============================================================================
// 说明：符合 golang-skills 函数式编程规范
// 1. 使用 candy 库进行集合操作
// 2. 使用 stringx 库进行字符串转换
// 3. 使用 osx 库进行文件操作

package main

import (
    "github.com/lazygophers/utils/candy"
    "github.com/lazygophers/utils/stringx"
    "github.com/lazygophers/utils/osx"
)

type User struct {
    Id   int64
    Name string
    Age  int
}

func ListActiveUsers(users []*User) []*User {
    return candy.Filter(users, func(u *User) bool {
        return u.Age >= 18
    })
}

func GetUserNames(users []*User) []string {
    return candy.Map(users, func(u *User) string {
        return u.Name
    })
}

func TransformFieldName(fieldName string) string {
    return stringx.ToSmallCamel(fieldName)
}

func LoadConfigFile(path string) error {
    if !osx.IsFile(path) {
        return osx.NewError("file not found")
    }
    return nil
}

// ============================================================================
// BAD EXAMPLE: 函数式编程
// ============================================================================
// 说明：不符合 golang-skills 函数式编程规范
// 1. 手动循环而非使用 candy
// 2. 手动实现字符串转换
// 3. 使用 os.Stat 而非 osx

package main

import (
    "fmt"
    "os"
    "strings"
)

type User struct {
    Id   int64
    Name string
    Age  int
}

func ListActiveUsers(users []*User) []*User {
    var activeUsers []*User
    for _, u := range users {
        if u.Age >= 18 {
            activeUsers = append(activeUsers, u)
        }
    }
    return activeUsers
}

func GetUserNames(users []*User) []string {
    var names []string
    for _, u := range users {
        names = append(names, u.Name)
    }
    return names
}

func TransformFieldName(fieldName string) string {
    parts := strings.Split(fieldName, "_")
    for i, part := range parts {
        parts[i] = strings.Title(part)
    }
    return strings.Join(parts, "")
}

func LoadConfigFile(path string) error {
    info, err := os.Stat(path)
    if err != nil && os.IsNotExist(err) {
        return fmt.Errorf("file not found")
    }
    _ = info
    return nil
}
