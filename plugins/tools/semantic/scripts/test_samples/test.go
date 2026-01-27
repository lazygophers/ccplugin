package main

import "fmt"

// Person 结构体
type Person struct {
	Name string
	Age  int
}

// Person 方法
func (p *Person) Greet() string {
	return fmt.Sprintf("Hello, I'm %s", p.Name)
}

// 普通函数
func CalculateSum(a int, b int) int {
	return a + b
}

// 接口
type Greeter interface {
	Greet() string
}

func main() {
	person := &Person{Name: "Alice", Age: 30}
	fmt.Println(person.Greet())
}
