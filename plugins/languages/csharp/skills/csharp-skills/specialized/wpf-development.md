# WPF 开发

## MVVM 模式

### ViewModelBase

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
```

### RelayCommand

```csharp
public class RelayCommand : ICommand
{
    private readonly Action _execute;
    private readonly Func<bool>? _canExecute;

    public RelayCommand(Action execute, Func<bool>? canExecute = null)
    {
        _execute = execute;
        _canExecute = canExecute;
    }

    public bool CanExecute(object? parameter) => _canExecute?.Invoke() ?? true;

    public void Execute(object? parameter) => _execute();

    public event EventHandler? CanExecuteChanged
    {
        add => CommandManager.RequerySuggested += value;
        remove => CommandManager.RequerySuggested -= value;
    }
}

public class RelayCommand<T> : ICommand
{
    private readonly Action<T?> _execute;
    private readonly Func<T?, bool>? _canExecute;

    public RelayCommand(Action<T?> execute, Func<T?, bool>? canExecute = null)
    {
        _execute = execute;
        _canExecute = canExecute;
    }

    public bool CanExecute(object? parameter) =>
        _canExecute?.Invoke((T?)parameter) ?? true;

    public void Execute(object? parameter) => _execute((T?)parameter);

    public event EventHandler? CanExecuteChanged
    {
        add => CommandManager.RequerySuggested += value;
        remove => CommandManager.RequerySuggested -= value;
    }
}
```

### 数据绑定

```xml
<!-- 绑定模式 -->
<TextBox Text="{Binding Username, UpdateSourceTrigger=PropertyChanged}" />
<TextBlock Text="{Binding FullName, Mode=OneWay}" />
<CheckBox IsChecked="{Binding IsEnabled, Mode=TwoWay}" />

<!-- 值转换 -->
<TextBlock Text="{Binding Date, StringFormat={}{0:yyyy-MM-dd}}" />
<TextBlock Text="{Binding Price, StringFormat=C}" />

<!-- 元素绑定 -->
<TextBox x:Name="UsernameTextBox" />
<TextBlock Text="{Binding Text, ElementName=UsernameTextBox}" />
```

## 资源和样式

```xml
<!-- 资源字典 -->
<ResourceDictionary xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
                    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <!-- 颜色资源 -->
    <SolidColorBrush x:Key="PrimaryBrush" Color="#0078D4" />
    <SolidColorBrush x:Key="SecondaryBrush" Color="#106EBE" />

    <!-- 样式 -->
    <Style TargetType="Button" x:Key="PrimaryButton">
        <Setter Property="Background" Value="{StaticResource PrimaryBrush}" />
        <Setter Property="Foreground" Value="White" />
        <Setter Property="Padding" Value="16,8" />
        <Setter Property="FontSize" Value="14" />
        <Setter Property="Cursor" Value="Hand" />
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="Button">
                    <Border Background="{TemplateBinding Background}"
                            Padding="{TemplateBinding Padding}"
                            CornerRadius="4">
                        <ContentPresenter HorizontalAlignment="Center"
                                        VerticalAlignment="Center" />
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>
</ResourceDictionary>
```

---

**最后更新**：2026-02-09
