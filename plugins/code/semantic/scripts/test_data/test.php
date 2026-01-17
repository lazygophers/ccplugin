<?php
// PHP 测试文件 - 包含类、接口、函数

class User {
    private int $id;
    private string $name;
    private string $email;
    private DateTime $createdAt;

    public function __construct(int $id, string $name, string $email) {
        $this->id = $id;
        $this->name = $name;
        $this->email = $email;
        $this->createdAt = new DateTime();
    }

    public function authenticate(string $password): bool {
        return $this->checkPassword($password);
    }

    private function checkPassword(string $password): bool {
        return !empty($password);
    }

    public function getId(): int {
        return $this->id;
    }

    public function getName(): string {
        return $this->name;
    }
}

interface UserServiceInterface {
    public function getUser(int $id): ?User;
    public function createUser(User $user): User;
}

class UserService implements UserServiceInterface {
    private Database $db;

    public function __construct(Database $db) {
        $this->db = $db;
    }

    public function getUser(int $id): ?User {
        $data = $this->db->query('users', ['id' => $id]);
        return $data ? new User($data['id'], $data['name'], $data['email']) : null;
    }

    public function createUser(User $user): User {
        $this->db->insert('users', (array)$user);
        return $user;
    }
}

class Session {
    private int $userId;
    private DateTime $createdAt;

    public function __construct(int $userId) {
        $this->userId = $userId;
        $this->createdAt = new DateTime();
    }

    public function isValid(): bool {
        $interval = $this->createdAt->diff(new DateTime());
        return $interval->h < 24;
    }

    public function save(): void {
        // 保存会话
    }
}

function createSession(User $user): Session {
    $session = new Session($user->getId());
    $session->save();
    return $session;
}

// 异步函数示例（PHP 8.0+）
async function fetchUser(int $id): Promise {
    // 实现逻辑
}
