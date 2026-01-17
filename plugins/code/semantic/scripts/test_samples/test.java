// 接口定义
interface Greeter {
    void greet();
}

// 类定义
class Person implements Greeter {
    private String name;
    private int age;

    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    @Override
    public void greet() {
        System.out.println("Hello, I'm " + name);
    }

    public String getName() {
        return name;
    }
}

// 枚举定义
enum Color {
    RED,
    GREEN,
    BLUE
}

public class Main {
    public static void main(String[] args) {
        Person person = new Person("Alice", 30);
        person.greet();

        Color color = Color.RED;
        System.out.println("Color: " + color);
    }
}
