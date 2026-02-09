# 框架开发

## ASP.NET Core

### Minimal API

```csharp
// ✅ Minimal API 设置
var builder = WebApplication.CreateBuilder(args);

// 服务注册
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddScoped<IUserService, UserService>();

var app = builder.Build();

// 端点定义
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

### 中间件

```csharp
// ✅ 自定义中间件
public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(
        RequestDelegate next,
        ILogger<ExceptionHandlingMiddleware> logger)
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

        var response = new
        {
            Status = false,
            Message = ex.Message
        };

        return context.Response.WriteAsJsonAsync(response);
    }
}

// 注册
app.UseMiddleware<ExceptionHandlingMiddleware>();
```

## Entity Framework Core

### DbContext 设置

```csharp
// ✅ DbContext 配置
public class ApplicationDbContext : DbContext
{
    public DbSet<User> Users { get; set; }
    public DbSet<Order> Orders { get; set; }

    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // 配置实体
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(x => x.Id);
            entity.Property(x => x.Email).IsRequired().HasMaxLength(256);
            entity.HasIndex(x => x.Email).IsUnique();
        });

        // 全局查询过滤器
        modelBuilder.Entity<User>()
            .HasQueryFilter(x => !x.IsDeleted);
    }
}
```

### 查询优化

```csharp
// ✅ 使用 AsNoTracking（只读）
public async Task<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// ✅ 使用 Include 预加载
public async Task<User?> GetUserWithOrdersAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .Include(u => u.Orders)
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// ✅ 使用 SplitQuery 避免笛卡尔积
public async Task<List<User>> GetUsersWithOrdersAsync(CancellationToken ct = default)
{
    return await _context.Users
        .Include(u => u.Orders)
        .AsSplitQuery()
        .ToListAsync(ct);
}
```

## WPF

### MVVM 模式

```csharp
// ✅ ViewModelBase
public abstract class ViewModelBase : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler? PropertyChanged;

    protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }

    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
            return false;

        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }
}

// ✅ 主 ViewModel
public class MainViewModel : ViewModelBase
{
    private string _title = "Welcome";
    public string Title
    {
        get => _title;
        set => SetProperty(ref _title, value);
    }

    public ICommand LoadCommand { get; }

    public MainViewModel()
    {
        LoadCommand = new AsyncRelayCommand(LoadAsync);
    }

    private async Task LoadAsync()
    {
        // 加载逻辑
    }
}
```

### 数据绑定

```xml
<!-- XAML 绑定 -->
<Window x:Class="MyApp.MainWindow">
    <Grid>
        <TextBox Text="{Binding Title, UpdateSourceTrigger=PropertyChanged}" />
        <Button Command="{Binding LoadCommand}" Content="Load" />
        <ListBox ItemsSource="{Binding Users}">
            <ListBox.ItemTemplate>
                <DataTemplate>
                    <StackPanel>
                        <TextBlock Text="{Binding Name}" />
                        <TextBlock Text="{Binding Email}" Foreground="Gray" />
                    </StackPanel>
                </DataTemplate>
            </ListBox.ItemTemplate>
        </ListBox>
    </Grid>
</Window>
```

## MAUI

### 页面和 ViewModel

```csharp
// ✅ ViewModel
public partial class HomePageViewModel : ObservableObject
{
    [ObservableProperty]
    private string _title = "Welcome";

    [ObservableProperty]
    private bool _isLoading;

    [RelayCommand]
    private async Task LoadAsync()
    {
        IsLoading = true;
        try
        {
            // 加载数据
        }
        finally
        {
            IsLoading = false;
        }
    }
}

// ✅ 页面代码后台
public partial class HomePage : ContentPage
{
    public HomePage(HomePageViewModel viewModel)
    {
        InitializeComponent();
        BindingContext = viewModel;
    }
}
```

## Blazor

### 组件

```razor
@* UserCard.razor *@
@using MyApp.Models

<div class="card">
    <h3>@User.Name</h3>
    <p>@User.Email</p>
    <button @onclick="ToggleDetails">Details</button>

    @if (showDetails)
    {
        <div>
            <p>Created: @User.CreatedAt.ToString("d")</p>
            <p>Status: @User.Status</p>
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

### 状态管理

```csharp
// ✅ 状态容器
public class AppState
{
    public User? CurrentUser { get; private set; }
    public event Action? OnChange;

    public void SetUser(User user)
    {
        CurrentUser = user;
        NotifyStateChanged();
    }

    private void NotifyStateChanged() => OnChange?.Invoke();
}

// ✅ 组件中使用
@inject AppState AppState

@code {
    protected override void OnInitialized()
    {
        AppState.OnChange += StateHasChanged;
    }

    public void Dispose()
    {
        AppState.OnChange -= StateHasChanged;
    }
}
```

---

**最后更新**：2026-02-09
