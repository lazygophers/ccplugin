// Package examples 展示 lazygophers-style 规范的实际应用（参考 Linky Server）
package examples

import (
	"errors"
	"time"

	// ✅ 必须使用 lazygophers 包库
	"github.com/lazygophers/log"
	"github.com/lazygophers/utils/candy"
)

// User 用户模型
type User struct {
	ID       int64
	Email    string
	Username string
	Age      int32
	IsActive bool
	Created  time.Time
	Updated  time.Time
}

// ✅ 全局状态模式（参考 Linky Server state/table.go）
// 存储所有有状态资源（数据库连接、缓存等）
var (
	// users - 全局用户数据访问（模拟数据库）
	users map[int64]*User = make(map[int64]*User)
)

// ============================================================================
// ✅ 函数式编程风格（99% 场景都应该这样做）
// ============================================================================

// UserLogin 用户登录
func UserLogin(email string) (*User, error) {
	// ✅ 直接遍历全局状态（函数式）
	for _, user := range users {
		if user.Email == email {
			log.Infof("user login success: %s", user.Username)
			return user, nil
		}
	}

	err := errors.New("user not found")
	log.Errorf("err:%v", err)
	return nil, err
}

// UserRegister 用户注册
func UserRegister(email, username string) (*User, error) {
	// ✅ 多行处理 + 日志（不包装）
	if email == "" {
		err := errors.New("email required")
		log.Errorf("err:%v", err)
		return nil, err
	}

	now := time.Now()
	user := &User{
		ID:       int64(len(users) + 1),
		Email:    email,
		Username: username,
		IsActive: true,
		Created:  now,
		Updated:  now,
	}

	// ✅ 多行处理 + 日志
	users[user.ID] = user
	log.Infof("user registered: %s", email)
	return user, nil
}

// GetUserByID 根据 ID 获取用户
func GetUserByID(id int64) (*User, error) {
	user, ok := users[id]
	if !ok {
		err := errors.New("user not found")
		log.Errorf("err:%v", err)
		return nil, err
	}
	return user, nil
}

// GetAllUsers 获取所有用户
func GetAllUsers() []*User {
	result := make([]*User, 0, len(users))
	for _, user := range users {
		result = append(result, user)
	}
	return result
}

// ListActiveUsers 获取活跃用户（使用 candy）
func ListActiveUsers(minAge int32) []*User {
	allUsers := GetAllUsers()

	// ✅ 必须使用 candy.Filter 而非手动循环
	activeUsers := candy.Filter(allUsers, func(u *User) bool {
		return u.IsActive && u.Age >= minAge
	})

	log.Infof("filtered %d active users (minAge=%d)", len(activeUsers), minAge)
	return activeUsers
}

// GetUserEmails 提取用户邮箱列表（使用 candy.Map）
func GetUserEmails(users []*User) []string {
	// ✅ 必须使用 candy.Map 而非手动循环
	emails := candy.Map(users, func(u *User) string {
		return u.Email
	})

	return emails
}

// GetUserStats 用户统计（纯函数式）
func GetUserStats() map[string]interface{} {
	allUsers := GetAllUsers()

	// ✅ 使用 candy 进行集合操作
	totalUsers := len(allUsers)

	// 统计成年用户
	adults := candy.Filter(allUsers, func(u *User) bool {
		return u.Age >= 18 && u.IsActive
	})

	// 提取年龄列表
	ages := candy.Map(allUsers, func(u *User) int32 {
		return u.Age
	})

	return map[string]interface{}{
		"total":  totalUsers,
		"adults": len(adults),
		"ages":   ages,
	}
}

// UpdateUserAge 更新用户年龄（纯函数）
func UpdateUserAge(id int64, newAge int32) (*User, error) {
	user, err := GetUserByID(id)
	if err != nil {
		log.Errorf("err:%v", err)
		return nil, err
	}

	// ✅ 更新用户
	user.Age = newAge
	user.Updated = time.Now()

	// ✅ 保存回全局状态
	users[id] = user
	log.Infof("user age updated: id=%d, age=%d", id, newAge)
	return user, nil
}

// ============================================================================
// ✅ 查询构建器模式（函数式链式调用）
// ============================================================================

type UserQuery struct {
	minAge    int32
	maxAge    int32
	isActive  *bool
	limit     int
	searchStr string
}

// NewUserQuery 创建查询构建器
func NewUserQuery() *UserQuery {
	return &UserQuery{
		limit: 10,
	}
}

// WithMinAge 添加最小年龄过滤
func (q *UserQuery) WithMinAge(age int32) *UserQuery {
	q.minAge = age
	return q
}

// WithMaxAge 添加最大年龄过滤
func (q *UserQuery) WithMaxAge(age int32) *UserQuery {
	q.maxAge = age
	return q
}

// WithActive 添加活跃状态过滤
func (q *UserQuery) WithActive(active bool) *UserQuery {
	q.isActive = &active
	return q
}

// WithLimit 限制结果数量
func (q *UserQuery) WithLimit(n int) *UserQuery {
	q.limit = n
	return q
}

// Execute 执行查询（链式调用最后执行）
func (q *UserQuery) Execute() []*User {
	allUsers := GetAllUsers()

	// ✅ 使用 candy.Filter 进行复杂过滤
	result := candy.Filter(allUsers, func(u *User) bool {
		// 年龄范围过滤
		if q.minAge > 0 && u.Age < q.minAge {
			return false
		}
		if q.maxAge > 0 && u.Age > q.maxAge {
			return false
		}

		// 活跃状态过滤
		if q.isActive != nil && u.IsActive != *q.isActive {
			return false
		}

		return true
	})

	// ✅ 限制结果
	if len(result) > q.limit {
		result = result[:q.limit]
	}

	return result
}

// ============================================================================
// 示例：纯函数式编程的优势
// ============================================================================

// Example_GetAdultEmails 获取成年用户的邮箱（纯函数式，零副作用）
func Example_GetAdultEmails() []string {
	return candy.Map(
		ListActiveUsers(18),  // 先过滤活跃且成年的用户
		func(u *User) string { // 再提取邮箱
			return u.Email
		},
	)
}

// Example_QueryUsers 查询用户示例（函数式链式调用）
func Example_QueryUsers() []*User {
	return NewUserQuery().
		WithMinAge(20).
		WithMaxAge(40).
		WithActive(true).
		WithLimit(10).
		Execute()
}

// ============================================================================
// ❌ 反面例子 - 不推荐（OOP 风格）
// ============================================================================

// ❌ 错误 - 创建显式的结构体和方法（OOP）
// 这会导致 99% 的代码都变成对象方法，失去函数式编程的优势
/*
type UserRepository struct {
	data map[int64]*User
}

func (r *UserRepository) GetByID(id int64) (*User, error) {
	// ...
}

func (r *UserRepository) GetAll() []*User {
	// ...
}
*/

// ❌ 错误 - 手动循环而不是使用 candy（不函数式）
func ListActiveUsersBad(users []*User, minAge int32) []*User {
	var result []*User
	for _, u := range users { // ❌ 不推荐
		if u.IsActive && u.Age >= minAge {
			result = append(result, u)
		}
	}
	return result
}

// ❌ 错误 - 手动提取字段而不是使用 candy（不函数式）
func GetEmailsBad(users []*User) []string {
	var emails []string
	for _, u := range users { // ❌ 不推荐
		emails = append(emails, u.Email)
	}
	return emails
}

// Init 初始化示例数据（仅用于演示）
func Init() error {
	// ✅ 初始化全局状态
	users = map[int64]*User{
		1: {
			ID:       1,
			Email:    "alice@example.com",
			Username: "alice",
			Age:      25,
			IsActive: true,
			Created:  time.Now(),
			Updated:  time.Now(),
		},
		2: {
			ID:       2,
			Email:    "bob@example.com",
			Username: "bob",
			Age:      30,
			IsActive: true,
			Created:  time.Now(),
			Updated:  time.Now(),
		},
	}

	log.Infof("example data initialized")
	return nil
}
