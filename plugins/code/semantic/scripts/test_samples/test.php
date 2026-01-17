<?php

// 接口定义
interface LoggerInterface {
    public function log(string $message): void;
}

// Trait 定义
trait Loggable {
    public function log(string $message): void {
        echo "[LOG] {$message}\n";
    }
}

// 类定义
class UserService implements LoggerInterface {
    use Loggable;

    private string $name;

    public function __construct(string $name) {
        $this->name = $name;
    }

    public function createUser(string $username): void {
        $this->log("Creating user: {$username}");
    }

    public function log(string $message): void {
        echo "[UserService] {$message}\n";
    }
}

// 函数定义
function calculateSum(int $a, int $b): int {
    return $a + $b;
}

// 执行代码
$service = new UserService("Admin");
$service->createUser("Alice");

$sum = calculateSum(5, 3);
echo "Sum: {$sum}\n";
?>
