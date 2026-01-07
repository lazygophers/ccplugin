package main

import (
	"fmt"
	"time"
)

// User 用户结构体
type User struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}

// NewUser 创建新用户
func NewUser(id int, name, email string) *User {
	return &User{
		ID:        id,
		Name:      name,
		Email:     email,
		CreatedAt: time.Now(),
	}
}

// Authenticate 验证用户方法（接收者示例）
func (u *User) Authenticate(password string) bool {
	// 验证逻辑
	return u.checkPassword(password)
}

// checkPassword 检查密码（私有方法）
func (u *User) checkPassword(password string) bool {
	// 密码验证逻辑
	return len(password) > 0
}

// UserService 用户服务接口
type UserService interface {
	GetUser(id int) (*User, error)
	CreateUser(user *User) error
}

// userService 用户服务实现
type userService struct {
	db *Database
}

// GetUser 获取用户
func (s *userService) GetUser(id int) (*User, error) {
	// 实现逻辑
	return &User{ID: id}, nil
}

// CreateUser 创建用户
func (s *userService) CreateUser(user *User) error {
	// 实现逻辑
	return nil
}

// NewUserService 创建用户服务
func NewUserService(db *Database) UserService {
	return &userService{db: db}
}
