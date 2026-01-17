// 类定义
class Person {
  String name;
  int age;

  Person(this.name, this.age);

  String greet() {
    return 'Hello, I\'m $name';
  }
}

// Mixin 定义
mixin Logger {
  void log(String message) {
    print('[LOG] $message');
  }
}

// 使用 Mixin 的类
class UserService with Logger {
  void createUser(String name) {
    log('Creating user: $name');
  }
}

// Extension 定义
extension StringExtension on String {
  String withPrefix() {
    return '>> $this';
  }
}

// 函数定义
int calculateSum(int a, int b) {
  return a + b;
}

void main() {
  final person = Person('Alice', 30);
  print(person.greet());

  final service = UserService();
  service.createUser('Bob');

  print('Hello'.withPrefix());

  final sum = calculateSum(5, 3);
  print('Sum: $sum');
}
