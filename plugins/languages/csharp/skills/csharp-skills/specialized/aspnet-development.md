# ASP.NET Core 开发

## Minimal API

### 端点定义

```csharp
var builder = WebApplication.CreateBuilder(args);

// 服务注册
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));
builder.Services.AddScoped<IUserService, UserService>();

var app = builder.Build();

// Swagger
app.UseSwagger();
app.UseSwaggerUI();

// 端点
app.MapGet("/api/users/{id:int}", async (
    int id,
    IUserService service,
    CancellationToken ct) =>
{
    var user = await service.GetUserAsync(id, ct);
    return user is not null ? Results.Ok(user) : Results.NotFound();
})
.WithName("GetUser")
.WithTags("Users");

app.MapPost("/api/users", async (
    User user,
    IUserService service,
    CancellationToken ct) =>
{
    var created = await service.CreateUserAsync(user, ct);
    return Results.Created($"/api/users/{created.Id}", created);
})
.WithName("CreateUser")
.WithTags("Users");

app.MapPut("/api/users/{id:int}", async (
    int id,
    User user,
    IUserService service,
    CancellationToken ct) =>
{
    user.Id = id;
    var updated = await service.UpdateUserAsync(user, ct);
    return Results.Ok(updated);
})
.WithName("UpdateUser")
.WithTags("Users");

app.MapDelete("/api/users/{id:int}", async (
    int id,
    IUserService service,
    CancellationToken ct) =>
{
    await service.DeleteUserAsync(id, ct);
    return Results.NoContent();
})
.WithName("DeleteUser")
.WithTags("Users");

app.Run();
```

## 中间件

```csharp
// ✅ 异常处理中间件
public class GlobalExceptionHandler
{
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionHandler> _logger;
    private readonly IHostEnvironment _env;

    public GlobalExceptionHandler(
        RequestDelegate next,
        ILogger<GlobalExceptionHandler> logger,
        IHostEnvironment env)
    {
        _next = next;
        _logger = logger;
        _env = env;
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

        var response = new
        {
            Status = false,
            Message = ex.Message
        };

        context.Response.StatusCode = ex switch
        {
            NotFoundException => StatusCodes.Status404NotFound,
            ValidationException => StatusCodes.Status400BadRequest,
            _ => StatusCodes.Status500InternalServerError
        };

        return context.Response.WriteAsJsonAsync(response);
    }
}

// 注册
app.UseMiddleware<GlobalExceptionHandler>();
```

## 请求验证

```csharp
// ✅ FluentValidation
public class CreateUserValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Email)
            .NotEmpty().WithMessage("Email is required")
            .EmailAddress().WithMessage("Email must be valid");

        RuleFor(x => x.Password)
            .NotEmpty().WithMessage("Password is required")
            .MinimumLength(8).WithMessage("Password must be at least 8 characters")
            .Matches("[A-Z]").WithMessage("Password must contain uppercase letter")
            .Matches("[a-z]").WithMessage("Password must contain lowercase letter")
            .Matches("[0-9]").WithMessage("Password must contain digit");
    }
}

// 端点中使用
app.MapPost("/api/users", async (
    CreateUserRequest request,
    IValidator<CreateUserRequest> validator,
    IUserService service,
    CancellationToken ct) =>
{
    var validationResult = await validator.ValidateAsync(request, ct);
    if (!validationResult.IsValid)
    {
        return Results.ValidationProblem(validationResult.ToDictionary());
    }

    var user = await service.CreateUserAsync(request, ct);
    return Results.Created($"/api/users/{user.Id}", user);
});
```

---

**最后更新**：2026-02-09
