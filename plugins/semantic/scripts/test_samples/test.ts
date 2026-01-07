// 接口定义
interface Person {
    name: string;
    age: number;
    greet(): string;
}

// 类型别名
type ID = string | number;

// 类定义
class UserService implements Person {
    name: string;
    age: number;

    constructor(name: string, age: number) {
        this.name = name;
        this.age = age;
    }

    greet(): string {
        return `Hello, I'm ${this.name}`;
    }

    createUser(id: ID, name: string): Person {
        console.log(`Creating user ${id}: ${name}`);
        return new UserService(name, 25);
    }
}

// 泛型函数
function getFirst<T>(arr: T[]): T | undefined {
    return arr[0];
}

// 箭头函数
const calculateSum = (a: number, b: number): number => {
    return a + b;
};

// 执行代码
const service = new UserService("Alice", 30);
console.log(service.greet());

const numbers = [1, 2, 3];
console.log(`First: ${getFirst(numbers)}`);
