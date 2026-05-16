---
name: csharp-desktop
description: |
  C# 桌面与跨平台 GUI 开发规范。覆盖 WPF / .NET MAUI / Avalonia UI / WinUI 3、
  CommunityToolkit.Mvvm source generators、MVVM 数据绑定、UI 线程调度、
  Dispatcher / MainThread、长任务取消、热重载、AOT 发布。当开发桌面应用、
  跨平台客户端、GUI 界面, 或说 "WPF"、"MAUI"、"Avalonia"、"WinUI"、"MVVM"、
  "XAML"、"数据绑定"、"DependencyProperty"、"ObservableProperty" 时加载。
allowed-tools: Read, Grep, Glob, Bash
---

# C# 桌面开发规范

跨平台桌面优先 Avalonia / .NET MAUI; Windows-only 业务桌面用 WPF; 新 Win 应用 WinUI 3 + WindowsAppSDK。

## 框架选型

| 场景 | 推荐 |
|------|------|
| 移动 + 桌面 (iOS/Android/Mac/Win) | .NET MAUI |
| 桌面跨平台 (Win/Mac/Linux) | Avalonia UI |
| Windows 现代应用 (MSIX) | WinUI 3 |
| Windows 传统业务、生态成熟 | WPF |

## MVVM 标配: CommunityToolkit.Mvvm

source generator 消除样板:

```csharp
public partial class OrderViewModel(IOrderService svc) : ObservableObject
{
    [ObservableProperty] private string _query = "";
    [ObservableProperty]
    [NotifyCanExecuteChangedFor(nameof(SearchCommand))]
    private bool _isLoading;
    public ObservableCollection<OrderDto> Items { get; } = [];

    [RelayCommand(CanExecute = nameof(CanSearch),
                  AllowConcurrentExecutions = false,
                  IncludeCancelCommand = true)]
    private async Task SearchAsync(CancellationToken ct)
    {
        IsLoading = true;
        try
        {
            Items.Clear();
            await foreach (var o in svc.SearchAsync(Query, ct))
                Items.Add(o);
        }
        finally { IsLoading = false; }
    }

    private bool CanSearch() => !IsLoading && !string.IsNullOrWhiteSpace(Query);
}
```

- ViewModel 不持有 UI 控件引用
- 命令用 `[RelayCommand]` 自动生成 `IAsyncRelayCommand` + 取消支持
- 属性变更 `[ObservableProperty]`; 联动通知 `[NotifyPropertyChangedFor]`
- 禁止手写 `INotifyPropertyChanged` 样板

## UI 线程调度

绝不在 UI 线程做阻塞 IO/CPU 工作。

| 框架 | 切回 UI 线程 |
|------|-------------|
| WPF | `Application.Current.Dispatcher.InvokeAsync` |
| WinUI 3 | `DispatcherQueue.TryEnqueue` |
| MAUI | `MainThread.BeginInvokeOnMainThread` |
| Avalonia | `Dispatcher.UIThread.InvokeAsync` |

异步事件处理器允许 `async void`, 但必须 `try/catch` 兜底, 错误送日志/UI 提示。

## 数据绑定

- 双向绑定限于真正双向的输入控件
- 复杂转换写 `IValueConverter`, 避免在 XAML 内联表达式过深
- 列表用 `ObservableCollection<T>`; 高频更新批量 (Avalonia `BatchUpdate`、WPF `CollectionViewSource.DeferRefresh`)
- WPF `UpdateSourceTrigger=PropertyChanged` 对实时校验有用, 但要权衡性能

## DI 与启动

```csharp
public partial class App : Application
{
    private readonly IHost _host = Host.CreateDefaultBuilder()
        .ConfigureServices(s =>
        {
            s.AddSingleton<MainWindow>();
            s.AddTransient<OrderViewModel>();
            s.AddHttpClient<IOrderService, OrderService>();
        })
        .Build();

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();
        _host.Services.GetRequiredService<MainWindow>().Show();
    }
}
```

MAUI: `MauiApp.CreateBuilder().UseMauiApp<App>().UseMauiCommunityToolkit()`。

## 资源与样式

- 全局样式放 `App.xaml` / `Application.Resources`
- 颜色/尺寸/字体走 `ResourceDictionary` + dynamic resource, 便于主题切换
- WPF 优先 `Style` + `ControlTemplate`; 不要直接改 control 默认 template 之外的内部结构

## 性能要点

- 启动: MAUI / WinUI 启用 AOT (`<PublishAot>true</PublishAot>` 或 ReadyToRun)
- 列表大数据: `Virtualization=true` + `ItemContainerStyle` 复用
- 图片缓存: MAUI 用 `Microsoft.Maui.Graphics`; Avalonia 用 `AsyncImageLoader`
- 不要在 `OnPropertyChanged` 跑重计算; 提取到 background task

## 长任务模式

```csharp
[RelayCommand(IncludeCancelCommand = true)]
private async Task ExportAsync(CancellationToken ct)
{
    Progress = 0;
    await foreach (var p in _exporter.RunAsync(ct))
        Progress = p;
}
```

`IncludeCancelCommand` 自动生成 `ExportCancelCommand`, 绑定到 UI 取消按钮。

## 测试

- ViewModel 用 xUnit + NSubstitute, 纯 .NET, 无需 UI runner
- UI 自动化: MAUI `Microsoft.Maui.TestUtils.DeviceTests`、WPF/WinUI 用 Appium、Avalonia 用 `Avalonia.Headless`
- ViewModel 必须能脱离视图实例化 (不依赖 `Application.Current`)

## 部署

- WPF: self-contained + ReadyToRun + SingleFile, `<TrimMode>partial</TrimMode>`
- MAUI: 各平台单独发布 (`dotnet publish -f net10.0-android` 等)
- WinUI: MSIX 包; 签名走 `Microsoft.Windows.SDK.BuildTools`

## 参考

- [.NET MAUI 文档](https://learn.microsoft.com/dotnet/maui/)
- [WPF 现代化](https://learn.microsoft.com/dotnet/desktop/wpf/)
- [Avalonia UI](https://docs.avaloniaui.net/)
- [CommunityToolkit.Mvvm](https://learn.microsoft.com/dotnet/communitytoolkit/mvvm/)
- [WinUI 3 (Windows App SDK)](https://learn.microsoft.com/windows/apps/winui/winui3/)
