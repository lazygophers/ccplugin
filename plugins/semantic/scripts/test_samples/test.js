// 类定义
class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    greet() {
        return `Hello, I'm ${this.name}`;
    }
}

// 箭头函数
const calculateSum = (a, b) => {
    return a + b;
};

// 普通函数
function createUser(name) {
    return new Person(name, 25);
}

// 对象解构
const { name, age } = { name: "Alice", age: 30 };

// 执行代码
const person = new Person("Bob", 28);
console.log(person.greet());

const sum = calculateSum(5, 3);
console.log(`Sum: ${sum}`);
