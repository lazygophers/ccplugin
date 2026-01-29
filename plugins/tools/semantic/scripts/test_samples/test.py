"""Python 测试文件"""


class Person:
    """Person 类"""

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, I'm {self.name}"


async def fetch_data(url: str) -> dict:
    """异步函数"""
    return {"data": "value"}


def calculate_sum(a: int, b: int) -> int:
    """计算和"""
    return a + b


if __name__ == "__main__":
    person = Person("Alice", 30)
    print(person.greet())
