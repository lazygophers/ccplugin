---
name: desktop
description: C# 桌面开发规范：WPF、MAUI、MVVM 模式。开发桌面应用时必须加载。
---

# C# 桌面开发规范

## 相关 Skills

| 场景     | Skill         | 说明                           |
| -------- | ------------- | ------------------------------ |
| 核心规范 | Skills(core)  | C# 12/.NET 8 标准、强制约定    |
| 异步编程 | Skills(async) | async/await、CancellationToken |

## MVVM 模式

```csharp
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
    }
}
```

## WPF 数据绑定

```xml
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

```csharp
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
        }
        finally
        {
            IsLoading = false;
        }
    }
}

public partial class HomePage : ContentPage
{
    public HomePage(HomePageViewModel viewModel)
    {
        InitializeComponent();
        BindingContext = viewModel;
    }
}
```

## 检查清单

- [ ] 使用 MVVM 模式
- [ ] ViewModel 实现 INotifyPropertyChanged
- [ ] 使用 ICommand 处理用户交互
- [ ] 数据绑定使用正确模式
- [ ] 异步操作使用 AsyncRelayCommand
