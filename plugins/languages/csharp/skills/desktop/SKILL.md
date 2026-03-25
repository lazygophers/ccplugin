---
name: desktop
description: C# 桌面开发规范 - WPF/.NET 8、.NET MAUI、Avalonia UI、WinUI 3、CommunityToolkit.Mvvm。开发桌面应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# 桌面开发规范

## 适用 Agents

- **csharp:dev** - 桌面应用开发
- **csharp:debug** - UI 线程调试、数据绑定问题

## 相关 Skills

- **Skills(csharp:core)** - 核心规范：C# 12/.NET 8 标准
- **Skills(csharp:async)** - 异步编程：UI 线程异步模式

## 框架选择指南（2024-2025）

| 框架 | 平台 | 推荐场景 |
|------|------|---------|
| WPF/.NET 8 | Windows | 企业桌面应用、复杂 UI |
| .NET MAUI | Android/iOS/Windows/macOS | 跨平台移动+桌面 |
| Avalonia UI | Windows/macOS/Linux/Web | 真正跨平台桌面 |
| WinUI 3 | Windows 10/11 | Windows 原生现代 UI |

## CommunityToolkit.Mvvm（推荐 MVVM 框架）

```csharp
// ✅ 使用 source generators 消除样板代码
public partial class MainViewModel : ObservableObject
{
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FullName))]
    private string _firstName = "";

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(FullName))]
    private string _lastName = "";

    [ObservableProperty]
    private bool _isLoading;

    public string FullName => $"{FirstName} {LastName}";

    [RelayCommand]
    private async Task LoadDataAsync(CancellationToken ct)
    {
        IsLoading = true;
        try
        {
            var data = await _dataService.GetDataAsync(ct);
            Items = new ObservableCollection<Item>(data);
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand(CanExecute = nameof(CanSave))]
    private async Task SaveAsync(CancellationToken ct)
    {
        await _dataService.SaveAsync(CurrentItem, ct);
    }

    private bool CanSave() => CurrentItem is not null && !IsLoading;
}

// ❌ 手动实现 INotifyPropertyChanged（冗余）
public class OldViewModel : INotifyPropertyChanged
{
    private string _name = "";
    public string Name
    {
        get => _name;
        set { _name = value; OnPropertyChanged(); }
    }
    // ... 大量样板代码
}
```

## WPF/.NET 8

```xml
<!-- ✅ 现代 WPF 数据绑定 -->
<Window x:Class="MyApp.MainWindow"
        xmlns:vm="clr-namespace:MyApp.ViewModels">
    <Window.DataContext>
        <vm:MainViewModel />
    </Window.DataContext>
    <Grid>
        <TextBox Text="{Binding FirstName, UpdateSourceTrigger=PropertyChanged}" />
        <TextBox Text="{Binding LastName, UpdateSourceTrigger=PropertyChanged}" />
        <TextBlock Text="{Binding FullName}" />
        <Button Command="{Binding LoadDataCommand}" Content="Load"
                IsEnabled="{Binding IsLoading, Converter={StaticResource InverseBoolConverter}}" />
        <ListBox ItemsSource="{Binding Items}">
            <ListBox.ItemTemplate>
                <DataTemplate>
                    <StackPanel Orientation="Horizontal">
                        <TextBlock Text="{Binding Name}" Margin="0,0,10,0" />
                        <TextBlock Text="{Binding Status}" Foreground="Gray" />
                    </StackPanel>
                </DataTemplate>
            </ListBox.ItemTemplate>
        </ListBox>
    </Grid>
</Window>
```

```csharp
// ✅ DI 配置（WPF + .NET 8）
public partial class App : Application
{
    private readonly IHost _host;

    public App()
    {
        _host = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddSingleton<MainViewModel>();
                services.AddSingleton<MainWindow>();
                services.AddHttpClient<IDataService, DataService>();
            })
            .Build();
    }

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();
        var mainWindow = _host.Services.GetRequiredService<MainWindow>();
        mainWindow.Show();
    }
}
```

## .NET MAUI

```csharp
// ✅ MAUI + CommunityToolkit.Mvvm
public partial class HomePageViewModel : ObservableObject
{
    private readonly IDataService _dataService;

    public HomePageViewModel(IDataService dataService)
    {
        _dataService = dataService;
    }

    [ObservableProperty]
    private ObservableCollection<Item> _items = [];

    [ObservableProperty]
    private bool _isRefreshing;

    [RelayCommand]
    private async Task RefreshAsync(CancellationToken ct)
    {
        IsRefreshing = true;
        try
        {
            var data = await _dataService.GetItemsAsync(ct);
            Items = new ObservableCollection<Item>(data);
        }
        finally
        {
            IsRefreshing = false;
        }
    }
}

// ✅ MAUI DI 注册
public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();
        builder.UseMauiApp<App>()
               .UseMauiCommunityToolkit();

        builder.Services.AddTransient<HomePageViewModel>();
        builder.Services.AddTransient<HomePage>();
        builder.Services.AddSingleton<IDataService, DataService>();

        return builder.Build();
    }
}
```

## Avalonia UI（跨平台桌面）

```csharp
// ✅ Avalonia + ReactiveUI
public class MainViewModel : ReactiveObject
{
    private string _searchText = "";
    public string SearchText
    {
        get => _searchText;
        set => this.RaiseAndSetIfChanged(ref _searchText, value);
    }

    public ReactiveCommand<Unit, List<Item>> SearchCommand { get; }

    public MainViewModel(ISearchService searchService)
    {
        SearchCommand = ReactiveCommand.CreateFromTask(
            () => searchService.SearchAsync(SearchText),
            this.WhenAnyValue(x => x.SearchText, text => !string.IsNullOrWhiteSpace(text)));
    }
}
```

## 异步 UI 模式

```csharp
// ✅ 正确的 UI 异步模式
public partial class DataViewModel : ObservableObject
{
    [RelayCommand]
    private async Task LoadAsync(CancellationToken ct)
    {
        // CommunityToolkit.Mvvm 自动处理 UI 线程调度
        IsLoading = true;
        try
        {
            // 后台线程执行
            var data = await Task.Run(() => HeavyComputation(), ct);
            // 自动回到 UI 线程
            Items = new ObservableCollection<Item>(data);
        }
        catch (OperationCanceledException) { /* 用户取消 */ }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
        finally
        {
            IsLoading = false;
        }
    }
}

// ❌ 在异步回调中直接访问 UI（不通过绑定）
// await Task.Run(() => textBox.Text = "done");  // 线程不安全！
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "手动实现 INPC 更灵活" | ✅ 是否用 CommunityToolkit.Mvvm source generators？ |
| "直接操作 UI 控件" | ✅ 是否通过数据绑定 + MVVM？ |
| "同步加载数据够快" | ✅ 长操作是否用 async + loading 状态？ |
| "不需要 DI" | ✅ 是否使用 Host.CreateDefaultBuilder DI？ |
| "WinForms 就够了" | ✅ 新项目是否用 WPF/MAUI/Avalonia？ |

## 检查清单

- [ ] 使用 CommunityToolkit.Mvvm（[ObservableProperty]、[RelayCommand]）
- [ ] MVVM 模式：View 不包含业务逻辑
- [ ] 使用 DI 管理 ViewModel 和 Service
- [ ] 长操作使用 async + IsLoading 状态
- [ ] 数据绑定使用正确的 UpdateSourceTrigger
- [ ] CancellationToken 支持取消操作
- [ ] 异步命令使用 [RelayCommand] + async Task
