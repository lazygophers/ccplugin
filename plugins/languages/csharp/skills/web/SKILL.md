---
name: csharp-web
description: |
  ASP.NET Core 10 Web 开发规范。覆盖 Minimal API、native AOT 发布、Blazor SSR /
  Streaming / Auto / Interactive 渲染模式、rate limiting、output caching、HybridCache、
  middleware 顺序、IExceptionHandler + ProblemDetails、OpenAPI 3.1、健康检查、
  JWT / Identity API、WebApplicationFactory 集成测试。
  当开发 Web API、REST 服务、Blazor 应用、配置中间件管道、调优 ASP.NET Core,
  或说 "ASP.NET Core"、"Minimal API"、"Blazor"、"middleware"、"WebApplication"、
  "AOT publish"、"HybridCache" 时加载。
allowed-tools: Read, Grep, Glob, Bash
---

# C# Web 开发规范

主流形态: Minimal API + EF Core + Blazor SSR。

## 项目骨架

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddProblemDetails()
    .AddOpenApi()                  // .NET 9+ 内置 (替代 Swashbuckle)
    .AddOutputCache()
    .AddHybridCache()              // .NET 10 GA, 替代 IDistributedCache
    .AddExceptionHandler<GlobalExceptionHandler>()
    .AddRateLimiter(o => o.AddFixedWindowLimiter("api", w =>
    {
        w.PermitLimit = 100;
        w.Window = TimeSpan.FromMinutes(1);
    }))
    .AddAuthentication().AddJwtBearer();

builder.Services.AddDbContextPool<AppDb>(o =>
    o.UseNpgsql(builder.Configuration.GetConnectionString("Db")));

var app = builder.Build();

app.UseExceptionHandler();      // 早期捕获
app.UseStatusCodePages();
app.UseHttpsRedirection();
app.UseRateLimiter();
app.UseAuthentication();
app.UseAuthorization();
app.UseOutputCache();
app.MapOpenApi();
app.MapHealthChecks("/health");
app.MapOrders();                // 扩展方法分组 endpoint
app.Run();

public partial class Program;   // 让集成测试可见
```

## Minimal API 组织

每个资源一个静态类, 扩展方法 + `MapGroup`:

```csharp
public static class OrderEndpoints
{
    public static IEndpointRouteBuilder MapOrders(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/api/orders")
                   .RequireAuthorization()
                   .RequireRateLimiting("api")
                   .WithTags("orders");

        g.MapGet("/{id:long}", GetById).WithName("GetOrder").CacheOutput();
        g.MapPost("/", Create).AddEndpointFilter<ValidationFilter>();
        return app;
    }

    static async Task<Results<Ok<OrderDto>, NotFound>> GetById(
        long id, IOrderService svc, CancellationToken ct) =>
        await svc.FindAsync(id, ct) is { } o ? TypedResults.Ok(o) : TypedResults.NotFound();
}
```

- 返回 `Results<T1, T2>` / `TypedResults.*` 让 OpenAPI 推断准确
- 不用 `Results.Ok` (非类型化), 用 `TypedResults.Ok`
- 参数绑定通过 `[FromBody]` / `[FromQuery]` / `[FromServices]` / `[AsParameters]`

## 异常处理: IExceptionHandler

```csharp
public class GlobalExceptionHandler(ILogger<GlobalExceptionHandler> logger) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext ctx, Exception ex, CancellationToken ct)
    {
        logger.LogError(ex, "Unhandled: {Message}", ex.Message);
        await Results.Problem(
            title: "Internal Server Error",
            statusCode: StatusCodes.Status500InternalServerError,
            extensions: new Dictionary<string, object?> { ["traceId"] = ctx.TraceIdentifier })
            .ExecuteAsync(ctx);
        return true;
    }
}
```

业务错误: endpoint 直接返回 `TypedResults.Problem(...)` / `ValidationProblem`。

## 模型验证

- DTO 用 `record` + `required` + 数据注解; 复杂规则用 `Microsoft.AspNetCore.Http.Validation` (.NET 10 内置) 或 FluentValidation
- 失败统一返回 ProblemDetails (`AddProblemDetails`)

## Native AOT (Minimal API)

```xml
<PublishAot>true</PublishAot>
```

要求:

- 不要 `Newtonsoft.Json`; 用 `System.Text.Json` source generator
- 移除反射 IOC; 优先 keyed services + source-generated registration
- `dotnet publish -c Release` 检查 `IL2026` / `IL3050` 警告

```csharp
[JsonSerializable(typeof(OrderDto))]
[JsonSerializable(typeof(CreateOrderDto))]
internal partial class AppJsonContext : JsonSerializerContext;

builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.TypeInfoResolverChain.Insert(0, AppJsonContext.Default));
```

## Blazor 渲染模式

| 模式 | 何时用 |
|------|--------|
| Static SSR | 列表/详情页面, 纯展示 |
| SSR Streaming (`[StreamRendering]`) | 大段数据分块渲染 |
| Interactive Server | 内网工具, 状态在服务端 |
| Interactive WebAssembly | 高交互、可离线 |
| Auto | SSR 首屏 + WebAssembly 接管 |

组件以 `@rendermode` 显式声明; 不要全站默认 Interactive。

## 中间件顺序

固定顺序: Exception → HTTPS → Static → Routing → CORS → AuthN → AuthZ → RateLimiter → OutputCache → Endpoints。
自定义中间件继承 `IMiddleware` (DI 友好) 而不是约定方法。

## 鉴权与授权

- JWT 优先 `AddJwtBearer`; Authority + Audience 必填
- 资源级授权用 `IAuthorizationHandler` + `OperationAuthorizationRequirement`
- 不要在 endpoint 手动 `User.HasClaim`, 用 policy
- `AddIdentityApiEndpoints<T>()` 提供注册/登录/MFA 全套 endpoint

## 缓存

- 短期响应缓存: Output Caching + `CacheOutput(...)`
- 应用级数据: **HybridCache** (.NET 10 GA) 同时利用 L1 内存 + L2 Redis, 替代 `IDistributedCache`

```csharp
var u = await cache.GetOrCreateAsync($"user:{id}",
    async ct => await db.Users.FindAsync([id], ct),
    tags: ["users"]);
```

## 可观测性

- OpenTelemetry: `AddOpenTelemetry().WithTracing().WithMetrics().WithLogs()`
- ASP.NET Core 内置 metrics: `Microsoft.AspNetCore.Hosting`、`Microsoft.AspNetCore.Server.Kestrel`
- 健康检查: liveness vs readiness 分开端点

## 测试

- 集成测试用 `WebApplicationFactory<Program>`; `Program` 加 `public partial class Program;`
- 替换外部依赖: `WithWebHostBuilder` + `ConfigureTestServices`
- 数据库用 TestContainers + Respawn 重置 (详见 csharp-data)

## 参考

- [ASP.NET Core 10 公告](https://devblogs.microsoft.com/dotnet/asp-net-core-10/)
- [Minimal APIs](https://learn.microsoft.com/aspnet/core/fundamentals/minimal-apis/)
- [Native AOT publishing](https://learn.microsoft.com/aspnet/core/fundamentals/native-aot)
- [Blazor render modes](https://learn.microsoft.com/aspnet/core/blazor/components/render-modes)
- [HybridCache](https://learn.microsoft.com/aspnet/core/performance/caching/hybrid)
- [Rate limiting middleware](https://learn.microsoft.com/aspnet/core/performance/rate-limit)
