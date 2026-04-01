---
description: "C# Web 开发规范：ASP.NET Core 8 Minimal APIs、native AOT 发布、Blazor SSR/Streaming 渲染、rate limiting 限流、output caching 缓存、middleware 中间件。开发 Web API、REST 服务、Blazor 应用时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# Web 开发规范

## 适用 Agents

- **csharp:dev** - Web API 开发
- **csharp:debug** - Web 应用调试
- **csharp:test** - 集成测试（WebApplicationFactory）

## 相关 Skills

- **Skills(csharp:core)** - 核心规范：C# 12/.NET 8 标准
- **Skills(csharp:async)** - 异步编程：async/await、CancellationToken
- **Skills(csharp:data)** - 数据访问：EF Core 8

## ASP.NET Core 8 Minimal APIs

```csharp
var builder = WebApplication.CreateBuilder(args);

// 服务注册
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddDbContext<AppDb>(o => o.UseSqlServer(connectionString));

// Rate limiting（.NET 8 内置）
builder.Services.AddRateLimiter(o =>
{
    o.AddFixedWindowLimiter("api", opt =>
    {
        opt.Window = TimeSpan.FromMinutes(1);
        opt.PermitLimit = 100;
    });
});

// Output caching（.NET 8 内置）
builder.Services.AddOutputCache(o =>
{
    o.AddBasePolicy(b => b.Expire(TimeSpan.FromMinutes(5)));
    o.AddPolicy("users", b => b.Tag("users").Expire(TimeSpan.FromMinutes(10)));
});

var app = builder.Build();

// ✅ Minimal API with TypedResults
app.MapGet("/api/users/{id:int}", async (
    int id,
    IUserService service,
    CancellationToken ct) =>
{
    var user = await service.GetUserAsync(id, ct);
    return user is not null
        ? TypedResults.Ok(user)
        : TypedResults.NotFound();
})
.WithName("GetUser")
.WithOpenApi()
.CacheOutput("users")
.RequireRateLimiting("api");

app.MapPost("/api/users", async (
    CreateUserRequest request,
    IUserService service,
    CancellationToken ct) =>
{
    var user = await service.CreateAsync(request, ct);
    return TypedResults.Created($"/api/users/{user.Id}", user);
})
.WithName("CreateUser")
.WithOpenApi()
.AddEndpointFilter<ValidationFilter>();

app.Run();
```

## Route Groups（组织端点）

```csharp
// ✅ 使用 MapGroup 组织相关端点
var users = app.MapGroup("/api/users")
    .RequireAuthorization()
    .RequireRateLimiting("api")
    .WithTags("Users");

users.MapGet("/", async (IUserService svc, CancellationToken ct) =>
    TypedResults.Ok(await svc.GetAllAsync(ct)));

users.MapGet("/{id:int}", async (int id, IUserService svc, CancellationToken ct) =>
    await svc.GetAsync(id, ct) is { } user
        ? TypedResults.Ok(user)
        : TypedResults.NotFound());

users.MapPost("/", async (CreateUserRequest req, IUserService svc, CancellationToken ct) =>
{
    var user = await svc.CreateAsync(req, ct);
    return TypedResults.Created($"/api/users/{user.Id}", user);
});
```

## Endpoint Filters（管道过滤器）

```csharp
// ✅ 验证过滤器
public class ValidationFilter : IEndpointFilter
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext ctx,
        EndpointFilterDelegate next)
    {
        // 自动验证请求参数
        foreach (var arg in ctx.Arguments)
        {
            if (arg is IValidatable validatable)
            {
                var errors = validatable.Validate();
                if (errors.Any())
                    return TypedResults.ValidationProblem(errors);
            }
        }
        return await next(ctx);
    }
}
```

## 异常处理中间件

```csharp
// ✅ .NET 8 IExceptionHandler（推荐）
public class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext context,
        Exception exception,
        CancellationToken ct)
    {
        logger.LogError(exception, "Unhandled exception: {Message}", exception.Message);

        var problem = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "Internal Server Error",
            Detail = exception.Message
        };

        context.Response.StatusCode = problem.Status.Value;
        await context.Response.WriteAsJsonAsync(problem, ct);
        return true;
    }
}

builder.Services.AddExceptionHandler<GlobalExceptionHandler>();
builder.Services.AddProblemDetails();
app.UseExceptionHandler();
```

## Blazor SSR + Streaming（.NET 8）

```razor
@* 服务端渲染 + 流式更新 *@
@page "/users"
@attribute [StreamRendering]

<h1>Users</h1>

@if (users is null)
{
    <p>Loading...</p>
}
else
{
    <ul>
        @foreach (var user in users)
        {
            <li>@user.Name - @user.Email</li>
        }
    </ul>
}

@code {
    private List<User>? users;

    protected override async Task OnInitializedAsync()
    {
        users = await UserService.GetAllAsync();
    }
}
```

## Native AOT 支持

```csharp
// ✅ AOT 友好的 Minimal API
var builder = WebApplication.CreateSlimBuilder(args);

// AOT 需要 source generator JSON
builder.Services.ConfigureHttpJsonOptions(o =>
{
    o.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonContext.Default);
});

var app = builder.Build();
app.MapGet("/", () => TypedResults.Ok(new { Message = "Hello AOT!" }));
app.Run();

// Source-generated JSON context
[JsonSerializable(typeof(User))]
[JsonSerializable(typeof(List<User>))]
internal partial class AppJsonContext : JsonSerializerContext;
```

## 安全（Identity + JWT）

```csharp
// ✅ .NET 8 Identity API endpoints
builder.Services.AddIdentityApiEndpoints<ApplicationUser>()
    .AddEntityFrameworkStores<AppDb>();

// ✅ JWT Bearer
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(o =>
    {
        o.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidAudience = builder.Configuration["Jwt:Audience"],
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };
    });

app.MapGroup("/identity").MapIdentityApi<ApplicationUser>();
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "Controller 更清晰" | ✅ 简单 API 是否用 Minimal APIs？ |
| "不需要 rate limiting" | ✅ 公开 API 是否配置 rate limiter？ |
| "缓存以后再加" | ✅ 读多写少端点是否用 output cache？ |
| "手动写异常处理" | ✅ 是否用 IExceptionHandler + ProblemDetails？ |
| "不需要 CancellationToken" | ✅ 端点是否接受 CancellationToken？ |
| "Results.Ok 就行" | ✅ 是否用 TypedResults 获得类型安全？ |

## 检查清单

- [ ] 使用 Minimal APIs（简单 API）
- [ ] 端点接受 CancellationToken
- [ ] 使用 TypedResults 替代 Results
- [ ] 使用 MapGroup 组织端点
- [ ] 配置 rate limiting
- [ ] 配置 output caching
- [ ] 使用 IExceptionHandler + ProblemDetails
- [ ] 启用 Swagger/OpenAPI
- [ ] 配置 Authentication/Authorization
- [ ] Health Checks 端点可用
