---
name: mermaid-class
description: Mermaid 类图语法规范，包括类定义、关系类型、可见性、泛型和注解等完整语法
---

# Mermaid 类图 (Class Diagram)

类图用于面向对象设计中展示类的结构、属性、方法以及类之间的关系。

## 基本语法

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
```

## 类定义

### 基本定义

```mermaid
classDiagram
    class Animal
    class Car
```

### 带标签的类

```mermaid
classDiagram
    class Animal["动物"]
    Animal : +String name
```

### 类成员

```mermaid
classDiagram
    class Animal {
        +String name
        -int age
        #String color
        +makeSound() void
        -calculateAge() int
    }
```

### 成员可见性

| 符号 | 可见性 | 说明 |
| --- | --- | --- |
| `+` | Public | 公有 |
| `-` | Private | 私有 |
| `#` | Protected | 保护 |
| `~` | Package/Internal | 包内 |

### 成员类型

```mermaid
classDiagram
    class Person {
        +String name
        +int age
        +List~String~ hobbies
        +Optional~Address~ address
    }
```

### 抽象方法

```mermaid
classDiagram
    class Shape {
        <<abstract>>
        +double area()*
        +double perimeter()*
    }
```

### 静态方法

```mermaid
classDiagram
    class Math {
        +static double PI$
        +static double sqrt(double)$
    }
```

## 类关系

### 关系类型

```mermaid
classDiagram
    A <|-- B : 继承
    C *-- D : 组合
    E o-- F : 聚合
    G --> H : 关联
    I -- J : 链接
    K <.. L : 依赖
    M <|.. N : 实现
```

| 关系 | 语法 | 说明 |
| --- | --- | --- |
| 继承 | `<|--` | 子类继承父类 |
| 组合 | `*--` | 强拥有关系 |
| 聚合 | `o--` | 弱拥有关系 |
| 关联 | `-->` | 一般关联 |
| 链接 | `--` | 简单链接 |
| 依赖 | `<..` | 依赖关系 |
| 实现 | `<|..` | 接口实现 |

### 关系标签

```mermaid
classDiagram
    Animal <|-- Dog : 继承
    Student --> Course : 选修
```

### 多重性

```mermaid
classDiagram
    Student "1" --> "n" Course : 选修
    Teacher "1..*" --> "1..*" Class : 授课
    Department "1" *-- "*" Employee : 雇佣
```

多重性符号：

| 符号 | 含义 |
| --- | --- |
| `1` | 有且仅有一个 |
| `0..1` | 零或一个 |
| `0..*` | 零或多个 |
| `1..*` | 一个或多个 |
| `n` | 多个 |
| `*` | 任意数量 |

## 泛型

```mermaid
classDiagram
    class Container~T~ {
        +T value
        +setValue(T value)
        +T getValue()
    }
    class List~Item~ {
        +add(Item item)
        +Item get(int index)
    }
```

## 注解

### 类注解

```mermaid
classDiagram
    class Shape {
        <<interface>>
        +double area()
    }
    class Animal {
        <<abstract>>
        +makeSound()
    }
    class Service {
        <<service>>
        +process()
    }
```

### 自定义注解

```mermaid
classDiagram
    class Cache {
        <<@Singleton>>
        +get(String key)
        +put(String key, Object value)
    }
```

## 命名空间

```mermaid
classDiagram
    namespace com.example {
        class User {
            +String name
        }
    }
    namespace com.service {
        class UserService {
            +getUser()
        }
    }
    User <.. UserService : 使用
```

## 方向

```mermaid
classDiagram
    direction TB
    class A
    class B
    A --> B
```

方向选项：
- `TB` - 从上到下
- `BT` - 从下到上
- `LR` - 从左到右
- `RL` - 从右到左

## 注释

```mermaid
classDiagram
    %% 这是注释
    class Animal {
        +String name
    }
```

## 最佳实践

### 命名规范

- 类名使用 PascalCase
- 属性和方法使用 camelCase
- 关系标签使用动词短语

### 设计建议

- 控制类的复杂度
- 合理使用可见性
- 明确关系类型

### 示例：完整类图

```mermaid
classDiagram
    direction TB

    class Animal {
        <<abstract>>
        +String name
        +int age
        +makeSound() void*
        +move() void
    }

    class Dog {
        +String breed
        +makeSound() void
        +fetch() void
    }

    class Cat {
        +boolean indoor
        +makeSound() void
        +climb() void
    }

    class Owner {
        +String name
        +List~Animal~ pets
        +addPet(Animal pet)
        +feedPets()
    }

    class Veterinarian {
        +String specialty
        +checkHealth(Animal animal)
        +vaccinate(Animal animal)
    }

    Animal <|-- Dog : 继承
    Animal <|-- Cat : 继承
    Owner "1" o-- "*" Animal : 拥有
    Veterinarian "1..*" --> "*" Animal : 治疗

    note for Animal "所有动物的基类"
```

## 参考链接

- [Mermaid 官方文档 - Class Diagram](https://mermaid.js.org/syntax/classDiagram.html)
