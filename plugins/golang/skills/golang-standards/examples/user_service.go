// Package examples 展示 golang-standards 规范的实际应用
package examples

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"
)

// User 代表一个用户（模型层）
type User struct {
	ID       int64  `json:"id" db:"id"`
	Email    string `json:"email" db:"email"`
	Password string `json:"password" db:"password"`
	Created  time.Time `json:"created" db:"created"`
	Updated  time.Time `json:"updated" db:"updated"`
}

// RegisterRequest 注册请求
type RegisterRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// Validate 验证注册请求
func (r *RegisterRequest) Validate() error {
	if len(r.Email) == 0 {
		return errors.New("email required")
	}
	if len(r.Password) < 8 {
		return errors.New("password too short (minimum 8 characters)")
	}
	return nil
}

// UserRepository 定义用户数据访问接口（Repository 层）
type UserRepository interface {
	GetByID(ctx context.Context, id int64) (*User, error)
	GetByEmail(ctx context.Context, email string) (*User, error)
	ExistsByEmail(ctx context.Context, email string) (bool, error)
	Save(ctx context.Context, user *User) error
	Update(ctx context.Context, user *User) error
	Delete(ctx context.Context, id int64) error
}

// UserService 业务逻辑层
type UserService struct {
	repo UserRepository
	// cache Cache  // 可添加缓存
	// logger Logger // 可添加日志
}

// NewUserService 创建用户服务
func NewUserService(repo UserRepository) *UserService {
	return &UserService{
		repo: repo,
	}
}

// Register 注册新用户
func (s *UserService) Register(ctx context.Context, req *RegisterRequest) (*User, error) {
	// 1. 验证输入
	if err := req.Validate(); err != nil {
		log.Printf("validation error: %v", err)
		return nil, fmt.Errorf("register validation: %w", err)
	}

	// 2. 检查邮箱是否已存在
	exists, err := s.repo.ExistsByEmail(ctx, req.Email)
	if err != nil {
		log.Printf("err:%v", err)
		return nil, fmt.Errorf("check email exists: %w", err)
	}
	if exists {
		return nil, errors.New("email already registered")
	}

	// 3. 创建用户
	now := time.Now()
	user := &User{
		Email:    req.Email,
		Password: hashPassword(req.Password), // 实际应该加密密码
		Created:  now,
		Updated:  now,
	}

	// 4. 保存到数据库
	if err := s.repo.Save(ctx, user); err != nil {
		log.Printf("err:%v", err)
		return nil, fmt.Errorf("save user: %w", err)
	}

	return user, nil
}

// GetUser 获取用户
func (s *UserService) GetUser(ctx context.Context, id int64) (*User, error) {
	user, err := s.repo.GetByID(ctx, id)
	if err != nil {
		log.Printf("err:%v", err)
		return nil, fmt.Errorf("get user: %w", err)
	}
	return user, nil
}

// UpdateUser 更新用户
func (s *UserService) UpdateUser(ctx context.Context, user *User) error {
	user.Updated = time.Now()

	if err := s.repo.Update(ctx, user); err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("update user: %w", err)
	}
	return nil
}

// DeleteUser 删除用户
func (s *UserService) DeleteUser(ctx context.Context, id int64) error {
	if err := s.repo.Delete(ctx, id); err != nil {
		log.Printf("err:%v", err)
		return fmt.Errorf("delete user: %w", err)
	}
	return nil
}

// hashPassword 模拟密码加密（实际应使用 bcrypt）
func hashPassword(password string) string {
	// 这里应该使用 bcrypt.GenerateFromPassword
	// 为简化示例，仅返回密码
	return password
}
