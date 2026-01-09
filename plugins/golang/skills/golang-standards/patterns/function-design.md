# 函数规范

## 核心原则

### ✅ 必须遵守

1. **动词开头** - 函数名以动词开头，清晰表达行为
2. **简洁签名** - 参数不超过 3 个，返回值不超过 2 个
3. **明确用途** - 函数职责单一，名字能清晰表达用途
4. **导出规范** - 导出函数用 PascalCase，非导出用 camelCase
5. **参数顺序** - context 优先，error 最后

### ❌ 禁止行为

- 使用 `Do`, `Execute`, `Process` 等模糊动词
- 函数签名过长（>3 个参数）
- 不相关的参数混合
- 使用 `interface{}` 做多个职责
- 缺少错误处理的函数无返回 error

## 函数命名规范

### 导出函数

```go
// ✅ 正确 - 明确的动词+名词
func Load(path string) (Config, error)
func Parse(data []byte) (*User, error)
func Generate(opts Options) (string, error)
func Validate(value string) error
func Hash(password string) string

// ✅ 特殊命名模式
func New(opts Options) (*Server, error)      // 构造函数
func NewWithConfig(cfg Config) *Server       // 带参数的构造
func Is(value string) bool                   // 布尔判断
func Has(key string) bool                    // 存在性检查
func Get(key string) (Value, bool)          // 安全获取
func Set(key, value string)                  // 设置值
func Add(item Item)                          // 添加
func Remove(id int)                          // 移除
func Count() int                             // 计数
func Find(criteria ...Criterion) []Item      // 查询

// ❌ 错误 - 模糊的动词
func Do(x interface{})
func Execute(interface{})
func Process(interface{})
func Handle(interface{})  // 如果用途不清
func Run()                // 模糊
```

### 非导出函数

```go
// ✅ 正确 - camelCase
func init(path string) error
func parseConfig() Config
func validateInput(input string) error
func extractUser(data []byte) (*User, error)

// ❌ 错误 - 大驼峰
func Init(path string) error
func ParseConfig() Config
```

## 函数签名设计

### 参数顺序（强制）

```go
// ✅ 标准顺序：context → 业务参数 → 配置 → error
func Process(ctx context.Context, item *Item, opts Options) error
func Query(ctx context.Context, id int, timeout time.Duration) (*Result, error)
func Create(ctx context.Context, req *CreateRequest) (*Response, error)

// ❌ 错误 - context 不在最前
func Process(item *Item, ctx context.Context) error
func Query(id int, ctx context.Context) (*Result, error)
```

### 参数数量规范

```go
// ✅ 优先 1-2 个参数
func Load(path string) Config
func Parse(data []byte) (*User, error)

// ✅ 最多 3 个参数
func Create(ctx context.Context, req *CreateRequest, opts Options) (*Response, error)

// ❌ 避免 - 参数过多
func Process(ctx context.Context, a, b, c int, d, e string, f bool) error
// 应该改为结构体
func Process(ctx context.Context, req *ProcessRequest) error
```

### 返回值规范

```go
// ✅ 标准返回：值 + error
func Load(path string) (*Config, error)
func Validate(value string) error
func Find(id int) (*Item, bool)  // 存在性返回 (value, ok)

// ❌ 避免 - 多个返回值
func LoadMultiple(path string) (*Config, *Data, error)
// 应该改为：
func Load(path string) (*ConfigWithData, error)
```

## API Handler 模式

### 标准 HTTP Handler（参考 Linky）

```go
// ✅ 接收 context + request struct
func (h *Handler) Register(ctx *fiber.Ctx) error {
    var req RegisterRequest
    if err := ctx.BodyParser(&req); err != nil {
        return h.error(ctx, http.StatusBadRequest, err)
    }

    // 业务逻辑
    user, err := h.service.Register(ctx.Context(), req)
    if err != nil {
        log.Errorf("err:%v", err)
        return h.error(ctx, http.StatusInternalServerError, err)
    }

    return ctx.JSON(http.StatusCreated, user)
}

// ❌ 避免 - 逐个参数
func (h *Handler) Register(ctx *fiber.Ctx, username, email string) error {}

// ❌ 避免 - 混合不同上下文
func (h *Handler) Register(r *http.Request, ctx context.Context) error {}
```

### 查询模式（Query Builder）

```go
// ✅ 链式查询构建器
type UserQuery struct {
    db    *gorm.DB
    age   int
    limit int
}

func NewUserQuery(db *gorm.DB) *UserQuery {
    return &UserQuery{db: db, limit: 10}
}

func (q *UserQuery) WithAge(age int) *UserQuery {
    q.age = age
    return q
}

func (q *UserQuery) Limit(n int) *UserQuery {
    q.limit = n
    return q
}

func (q *UserQuery) Find() ([]*User, error) {
    query := q.db
    if q.age > 0 {
        query = query.Where("age = ?", q.age)
    }
    return query.Limit(q.limit).Find(&[]*User{})
}

// 使用
users, err := NewUserQuery(db).WithAge(18).Limit(20).Find()
```

## 设计模式

### 工厂函数（Factory）

```go
// ✅ 标准工厂函数
func NewServer(cfg Config) *Server {
    return &Server{
        addr:    cfg.Addr,
        timeout: cfg.Timeout,
    }
}

func NewServerWithDefaults(addr string) *Server {
    return NewServer(Config{
        Addr:    addr,
        Timeout: 30 * time.Second,
    })
}

// ❌ 避免 - 混合 New 和初始化
func NewServer(cfg Config) *Server {
    s := &Server{...}
    s.Start()  // 不应该在 New 中启动
    return s
}
```

### 状态获取器

```go
// ✅ 明确的 Get 方法
func (s *Server) GetConfig() Config {
    return s.config
}

func (s *Server) GetStatus() Status {
    return s.status
}

// 或带存在性检查
func (s *Server) GetUser(id int) (*User, bool) {
    user, ok := s.users[id]
    return user, ok
}

// ❌ 避免 - 通用的 Get
func (s *Server) Get(key string) interface{} {}
```

### 验证函数

```go
// ✅ 明确的验证
func Validate(password string) error {
    if len(password) < 8 {
        return ErrPasswordTooShort
    }
    return nil
}

// 或布尔值判断
func IsValid(password string) bool {
    return len(password) >= 8
}

// ❌ 避免 - 返回 interface{}
func Check(password interface{}) interface{} {}
```

## 高级模式

### 选项模式（Options Pattern）

```go
// ✅ 使用选项函数
type ServerOptions struct {
    Timeout   time.Duration
    MaxConns  int
    TLS       bool
}

type ServerOption func(*ServerOptions)

func WithTimeout(d time.Duration) ServerOption {
    return func(opts *ServerOptions) {
        opts.Timeout = d
    }
}

func WithMaxConns(n int) ServerOption {
    return func(opts *ServerOptions) {
        opts.MaxConns = n
    }
}

func NewServer(opts ...ServerOption) *Server {
    defaultOpts := &ServerOptions{
        Timeout:  30 * time.Second,
        MaxConns: 100,
    }
    for _, opt := range opts {
        opt(defaultOpts)
    }
    return &Server{...}
}

// 使用
server := NewServer(
    WithTimeout(60*time.Second),
    WithMaxConns(200),
)
```

### 中间件模式

```go
// ✅ 链式中间件
type Handler func(ctx *fiber.Ctx) error

func Middleware(h Handler) Handler {
    return func(ctx *fiber.Ctx) error {
        // 前置处理
        if err := validate(ctx); err != nil {
            return err
        }

        // 调用处理器
        if err := h(ctx); err != nil {
            return err
        }

        // 后置处理
        return nil
    }
}

// 使用
handler := Middleware(Auth(Logger(handler)))
```

## 最佳实践

### 1. 函数越短越好

```go
// ✅ 短而专一
func (h *Handler) Register(ctx *fiber.Ctx) error {
    var req RegisterRequest
    if err := ctx.BodyParser(&req); err != nil {
        return h.error(ctx, http.StatusBadRequest, err)
    }
    return h.register(ctx)
}

func (h *Handler) register(ctx *fiber.Ctx) error {
    req := getRequest(ctx)  // 提取逻辑
    user, err := h.service.Register(ctx.Context(), req)
    if err != nil {
        return h.error(ctx, http.StatusInternalServerError, err)
    }
    return ctx.JSON(http.StatusOK, user)
}

// ❌ 避免 - 过长
func (h *Handler) Register(ctx *fiber.Ctx) error {
    // 50 行处理逻辑...
}
```

### 2. 纯函数优先

```go
// ✅ 纯函数 - 无副作用
func Sum(a, b int) int {
    return a + b
}

// ✅ 明确副作用
func (s *Server) Store(key string, value interface{}) {
    s.cache[key] = value  // 明确修改状态
}

// ❌ 隐藏副作用
func Process(data []int) int {
    s := &globalState
    s.count += len(data)  // 隐藏副作用
    return sum(data)
}
```

### 3. 文档注释

```go
// ✅ 导出函数必有注释
// Register 注册新用户，返回用户信息和错误
func Register(ctx context.Context, req *RegisterRequest) (*User, error)

// ✅ 复杂函数说明参数
// Find 根据条件查询用户
//
// age: 年龄过滤条件，为 0 时不过滤
// limit: 最多返回 limit 条记录，为 0 时返回全部
func Find(age, limit int) ([]*User, error)

// ❌ 避免 - 无注释
func Register(ctx context.Context, req *RegisterRequest) (*User, error)
```

## 参考

- [Effective Go - Functions](https://golang.org/doc/effective_go#functions)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Linky 服务器 API handlers](../../../references/linky-server-patterns.md)
