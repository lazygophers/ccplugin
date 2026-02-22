---
name: web
description: C# Web 开发规范：ASP.NET Core、Minimal API、Blazor。开发 Web 应用时必须加载。
---

# C# Web 开发规范

## 相关 Skills

| 场景     | Skill         | 说明                           |
| -------- | ------------- | ------------------------------ |
| 核心规范 | Skills(core)  | C# 12/.NET 8 标准、强制约定    |
| 异步编程 | Skills(async) | async/await、CancellationToken |
| 数据访问 | Skills(data)  | Entity Framework Core          |

## Minimal API

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddScoped<IUserService, UserService>();

var app = builder.Build();

app.MapGet("/api/users/{id}", async (int id, IUserService service, CancellationToken ct) =>
{
    var user = await service.GetUserAsync(id, ct);
    return user is not null ? Results.Ok(user) : Results.NotFound();
})
.WithName("GetUser")
.WithOpenApi();

app.MapPost("/api/users", async (User user, IUserService service, CancellationToken ct) =>
{
    var created = await service.CreateUserAsync(user, ct);
    return Results.Created($"/api/users/{created.Id}", created);
});

app.Run();
```

## 中间件

```csharp
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception ex)
    {
        context.Response.ContentType = "application/json";
        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        return context.Response.WriteAsJsonAsync(new { Status = false, Message = ex.Message });
    }
}

app.UseMiddleware<ExceptionHandlingMiddleware>();
```

## Blazor 组件

```razor
@* UserCard.razor *@
<div class="card">
    <h3>@User.Name</h3>
    <p>@User.Email</p>
    <button @onclick="ToggleDetails">Details</button>

    @if (showDetails)
    {
        <div>
            <p>Created: @User.CreatedAt.ToString("d")</p>
        </div>
    }
</div>

@code {
    [Parameter]
    public User User { get; set; } = default!;

    private bool showDetails;

    private void ToggleDetails() => showDetails = !showDetails;
}
```

## 检查清单

- [ ] 使用 Minimal API
- [ ] 端点传递 CancellationToken
- [ ] 使用异常处理中间件
- [ ] 启用 Swagger
- [ ] 使用依赖注入
