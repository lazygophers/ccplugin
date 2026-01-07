// TypeScript 测试文件 - 包含接口、类、泛型、类型注解

interface User {
  id: number;
  name: string;
  email: string;
  createdAt?: Date;
}

interface UserService {
  getUser(id: number): Promise<User | null>;
  createUser(user: User): Promise<User>;
}

class UserServiceImpl implements UserService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  async getUser(id: number): Promise<User | null> {
    const data = await this.db.query('users', { where: { id } });
    return data ? this.mapToUser(data) : null;
  }

  async createUser(user: User): Promise<User> {
    await this.db.insert('users', user);
    return user;
  }

  private mapToUser(data: any): User {
    return {
      id: data.id,
      name: data.name,
      email: data.email,
      createdAt: new Date(data.createdAt),
    };
  }
}

class Session {
  readonly userId: number;
  readonly createdAt: Date;
  private _valid: boolean = true;

  constructor(userId: number) {
    this.userId = userId;
    this.createdAt = new Date();
  }

  get isValid(): boolean {
    const hours = (Date.now() - this.createdAt.getTime()) / (1000 * 60 * 60);
    return hours < 24 && this._valid;
  }

  async save(): Promise<void> {
    // 保存会话
  }

  invalidate(): void {
    this._valid = false;
  }
}

// 泛型函数示例
async function fetchEntity<T>(
  id: number,
  mapper: (data: any) => T
): Promise<T | null> {
  const response = await fetch(`/api/entities/${id}`);
  const data = await response.json();
  return mapper(data);
}

// 类型别名示例
type UserId = number;
type SessionId = string;

// 联合类型示例
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: Error };
