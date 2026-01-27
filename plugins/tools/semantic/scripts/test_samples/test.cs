// 接口定义
public interface IGreeter
{
    void Greet();
}

// 类定义
public class Person : IGreeter
{
    public string Name { get; set; }
    public int Age { get; set; }

    public Person(string name, int age)
    {
        Name = name;
        Age = age;
    }

    public void Greet()
    {
        Console.WriteLine($"Hello, I'm {Name}");
    }

    public string GetInfo()
    {
        return $"{Name}, {Age} years old";
    }
}

// 枚举定义
public enum Color
{
    Red,
    Green,
    Blue
}

// 泛型类
public class Repository<T>
{
    private List<T> _items = new List<T>();

    public void Add(T item)
    {
        _items.Add(item);
    }

    public T Find(Func<T, bool> predicate)
    {
        return _items.FirstOrDefault(predicate);
    }
}

// 异步方法示例
public class UserService
{
    public async Task<Person> GetUserAsync(string name)
    {
        await Task.Delay(100); // 模拟异步操作
        return new Person(name, 25);
    }

    public async Task<IEnumerable<Person>> GetAllUsersAsync()
    {
        await Task.Delay(100);
        return new List<Person>
        {
            new Person("Alice", 30),
            new Person("Bob", 25)
        };
    }
}

// 记录 (Record, C# 9.0+)
public record Config(string Version, string Environment);

// 扩展方法
public static class StringExtensions
{
    public static string PrintWithPrefix(this string s)
    {
        return $">> {s}";
    }
}

public class Program
{
    public static void Main(string[] args)
    {
        // 基本使用
        var person = new Person("Alice", 30);
        person.Greet();
        Console.WriteLine(person.GetInfo());

        // 枚举使用
        var color = Color.Red;
        Console.WriteLine($"Color: {color}");

        // 泛型使用
        var repo = new Repository<Person>();
        repo.Add(person);
        var found = repo.Find(p => p.Name == "Alice");
        Console.WriteLine($"Found: {found?.Name}");

        // 记录使用
        var config = new Config("1.0.0", "Production");
        Console.WriteLine($"Config: {config.Version}");

        // 扩展方法使用
        Console.WriteLine("Hello".PrintWithPrefix());

        // LINQ 查询
        var users = new List<Person>
        {
            new Person("Alice", 30),
            new Person("Bob", 25),
            new Person("Charlie", 35)
        };

        var adults = users.Where(u => u.Age >= 30).ToList();
        Console.WriteLine($"Adults: {adults.Count}");
    }
}
