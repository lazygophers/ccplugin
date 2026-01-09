# Lazygophers 函数设计规范

## 核心原则

### ✅ 必须遵守

1. **零分配优先** - 设计函数时优先考虑内存分配
2. **函数式风格** - 优先使用 candy 库进行集合操作
3. **简洁签名** - 参数不超过 3 个，使用结构体传递多个参数
4. **查询构建器** - 复杂操作使用链式调用
5. **状态提取** - API handlers 中优先从 context 提取状态

## 零分配函数设计

### 避免分配

```go
// ✅ 减少分配的设计
type Query struct {
    filter string
    limit  int
}

func (q *Query) WithFilter(f string) *Query {
    q.filter = f
    return q
}

func (q *Query) Execute() ([]Item, error) {
    // 查询逻辑
    return items, nil
}

// ✅ 使用内存池减少分配
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processData(data []byte) string {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer bufferPool.Put(buf)
    buf.Reset()

    buf.Write(data)
    return buf.String()
}

// ❌ 避免 - 每次创建新缓冲区
func processDataBad(data []byte) string {
    buf := new(bytes.Buffer)  // 每次分配
    buf.Write(data)
    return buf.String()
}
```

## 函数式编程（Candy 风格）

### 集合操作必用 Candy

```go
import "github.com/lazygophers/utils/candy"

// ✅ 必须使用 candy 而非手动循环
func (h *Handler) ListActiveUsers(ctx context.Context) ([]*User, error) {
    users, err := h.repo.GetAll(ctx)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    // ✅ 使用 candy.Filter
    activeUsers := candy.Filter(users, func(u *User) bool {
        return u.IsActive
    })

    // ✅ 使用 candy.Map 转换
    emails := candy.Map(activeUsers, func(u *User) string {
        return u.Email
    })

    _ = emails
    return activeUsers, nil
}

// ❌ 禁止 - 手动循环
func ListActiveUsersBad(ctx context.Context) []*User {
    var result []*User
    for _, u := range users {
        if u.IsActive {
            result = append(result, u)  // 不推荐
        }
    }
    return result
}
```

### 字符串转换必用 Stringx

```go
import "github.com/lazygophers/utils/stringx"

// ✅ 必须使用 stringx
func (h *Handler) TransformField(fieldName string) string {
    return stringx.ToSmallCamel(fieldName)  // 用户名 → userName
}

// ❌ 禁止 - 手动实现
func TransformFieldBad(fieldName string) string {
    // 不要自己实现字符串转换
    return "" // 省略...
}
```

### 文件操作必用 Osx

```go
import "github.com/lazygophers/utils/osx"

// ✅ 必须使用 osx
func (h *Handler) LoadConfigFile(path string) error {
    if !osx.IsFile(path) {
        return fmt.Errorf("config file not found: %s", path)
    }

    data, err := os.ReadFile(path)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    return h.parseConfig(data)
}

// ❌ 禁止 - 使用 os.Stat
func LoadConfigFileBad(path string) error {
    info, err := os.Stat(path)
    if err != nil && os.IsNotExist(err) {
        return fmt.Errorf("file not found")
    }
    // ...
}
```

## 函数签名设计（参考 Linky API Handler）

### API Handler 模式

```go
// ✅ API handlers - 接受 context + request struct
type Handler struct {
    service UserService
}

func (h *Handler) Register(ctx *fiber.Ctx) error {
    var req RegisterRequest
    if err := ctx.BodyParser(&req); err != nil {
        log.Errorf("err:%v", err)
        return h.error(ctx, http.StatusBadRequest, err)
    }

    user, err := h.service.Register(ctx.Context(), &req)
    if err != nil {
        log.Errorf("err:%v", err)
        return h.error(ctx, http.StatusInternalServerError, err)
    }

    return ctx.JSON(http.StatusCreated, user)
}

// ❌ 避免 - 逐个参数
func (h *Handler) RegisterBad(ctx *fiber.Ctx, username, email string) error {}
```

### Service 层函数

```go
// ✅ Service 函数 - context 优先
func (s *UserService) Register(ctx context.Context, req *RegisterRequest) (*User, error) {
    if err := req.Validate(); err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    exists, err := s.repo.ExistsByEmail(ctx, req.Email)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    if exists {
        return nil, errors.New("email already registered")
    }

    user := &User{
        Email: req.Email,
    }
    if err := s.repo.Save(ctx, user); err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return user, nil
}

// ✅ 查询函数 - 查询构建器模式
type UserQuery struct {
    db   DB
    age  int
    limit int
}

func NewUserQuery(db DB) *UserQuery {
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

func (q *UserQuery) Find(ctx context.Context) ([]*User, error) {
    query := q.db.Query()
    if q.age > 0 {
        query = query.Where("age = ?", q.age)
    }

    var users []*User
    err := query.Limit(q.limit).Scan(&users).Error
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return users, nil
}

// 使用
users, err := NewUserQuery(db).WithAge(18).Limit(20).Find(ctx)
```

## 状态提取函数（参考 Linky）

### 从 Context 提取状态

```go
// ✅ 标准的状态提取模式
func (h *Handler) GetCurrentUser(ctx *fiber.Ctx) (*User, error) {
    // 从 context 中提取用户信息
    uid, ok := ctx.Locals("uid").(int64)
    if !ok {
        return nil, errors.New("unauthorized")
    }

    user, err := h.service.GetUser(ctx.Context(), uid)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return user, nil
}

// ✅ 中间件设置状态
func Auth(h Handler) Handler {
    return func(ctx *fiber.Ctx) error {
        token := ctx.Get("Authorization")
        // 验证 token
        uid := parseToken(token)
        ctx.Locals("uid", uid)  // 设置状态
        return h(ctx)
    }
}
```

## 高级设计模式

### 策略模式（参考 Linky 命名风格处理）

```go
// ✅ 策略模式处理不同的实现
type Processor interface {
    Process(data string) string
}

var Processors = map[string]Processor{
    "camel": &CamelProcessor{},
    "snake": &SnakeProcessor{},
}

type CamelProcessor struct{}

func (p *CamelProcessor) Process(data string) string {
    return stringx.ToSmallCamel(data)
}

type SnakeProcessor struct{}

func (p *SnakeProcessor) Process(data string) string {
    return stringx.ToSnake(data)
}

// 使用
processor := Processors["camel"]
result := processor.Process("user_name")  // userName
```

### 选项模式

```go
// ✅ 使用选项函数处理可选参数
type ServiceOptions struct {
    Logger Logger
    Timeout time.Duration
}

type ServiceOption func(*ServiceOptions)

func WithLogger(logger Logger) ServiceOption {
    return func(opts *ServiceOptions) {
        opts.Logger = logger
    }
}

func NewService(opts ...ServiceOption) *Service {
    defaultOpts := &ServiceOptions{
        Timeout: 30 * time.Second,
    }
    for _, opt := range opts {
        opt(defaultOpts)
    }
    return &Service{opts: defaultOpts}
}

// 使用
service := NewService(WithLogger(logger))
```

## 性能考虑

### 内存优化函数

```go
// ✅ 使用指针接收者避免复制
type Request struct {
    Data []byte
}

func (r *Request) Process() error {
    // 处理 r.Data，避免复制大对象
    return nil
}

// ✅ 预分配容量
func ProcessItems(items []Item) []string {
    result := make([]string, 0, len(items))  // 预分配
    for _, item := range items {
        result = append(result, item.String())
    }
    return result
}

// ❌ 避免 - 无容量预分配
func ProcessItemsBad(items []Item) []string {
    var result []string  // 容量为 0
    for _, item := range items {
        result = append(result, item.String())  // 多次重新分配
    }
    return result
}
```

### 避免不必要的复制

```go
// ✅ 共享而非复制
type Data struct {
    Values []int
}

func (d *Data) Sum() int {
    total := 0
    for _, v := range d.Values {
        total += v
    }
    return total
}

// ❌ 避免 - 复制整个切片
func (d Data) SumBad() int {  // 值接收者
    total := 0
    for _, v := range d.Values {
        total += v
    }
    return total
}
```

## 参考

- [Lazygophers Utils](https://github.com/lazygophers/utils)
- [Candy Documentation](https://github.com/lazygophers/utils/tree/master/candy)
- [Linky Server 参考](../references.md)
