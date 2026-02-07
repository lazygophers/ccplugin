// ============================================================================
// GOOD EXAMPLE: 项目结构
// ============================================================================
// 说明：符合 golang-skills 项目结构规范
// 1. 三层架构：API → Impl → State
// 2. 全局状态模式
// 3. 单向依赖

package main

import (
    "github.com/lazygophers/log"
    "github.com/gofiber/fiber/v2"
)

// State 层：全局状态
var (
    User *UserModel
)

type UserModel struct{}

func (m *UserModel) GetById(id int64) (*User, error) {
    return &User{Id: id}, nil
}

// Impl 层：业务逻辑
func UserLogin(req *LoginReq) (*User, error) {
    user, err := User.GetById(req.Id)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return user, nil
}

// API 层：HTTP 路由
func SetupRoutes(app *fiber.App) {
    app.Post("/api/user/login", func(ctx *fiber.Ctx) error {
        var req LoginReq
        if err := ctx.BodyParser(&req); err != nil {
            log.Errorf("err:%v", err)
            return err
        }

        user, err := UserLogin(&req)
        if err != nil {
            log.Errorf("err:%v", err)
            return err
        }

        return ctx.JSON(user)
    })
}

type User struct {
    Id   int64
    Name string
}

type LoginReq struct {
    Id int64
}

// ============================================================================
// BAD EXAMPLE: 项目结构
// ============================================================================
// 说明：不符合 golang-skills 项目结构规范
// 1. 使用 Repository 接口
// 2. 依赖注入
// 3. 循环依赖

package main

import (
    "github.com/lazygophers/log"
    "github.com/gofiber/fiber/v2"
)

// State 层：使用 Repository 接口
type UserRepository interface {
    GetById(id int64) (*User, error)
}

type UserModel struct{}

func (m *UserModel) GetById(id int64) (*User, error) {
    return &User{Id: id}, nil
}

// Impl 层：依赖注入
type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

func (s *UserService) Login(req *LoginReq) (*User, error) {
    user, err := s.repo.GetById(req.Id)
    if err != nil {
        return nil, err
    }
    return user, nil
}

// API 层：依赖注入
type UserHandler struct {
    service *UserService
}

func NewUserHandler(service *UserService) *UserHandler {
    return &UserHandler{service: service}
}

func (h *UserHandler) Login(ctx *fiber.Ctx) error {
    var req LoginReq
    if err := ctx.BodyParser(&req); err != nil {
        return err
    }

    user, err := h.service.Login(&req)
    if err != nil {
        return err
    }

    return ctx.JSON(user)
}

type User struct {
    Id   int64
    Name string
}

type LoginReq struct {
    Id int64
}
