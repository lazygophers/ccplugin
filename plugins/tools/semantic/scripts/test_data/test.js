// JavaScript 测试文件 - 包含类、箭头函数、异步函数

class User {
  constructor(id, name, email) {
    this.id = id;
    this.name = name;
    this.email = email;
    this.createdAt = new Date();
  }

  authenticate(password) {
    return this.checkPassword(password);
  }

  checkPassword(password) {
    return password && password.length > 0;
  }

  async save() {
    // 保存用户
    return true;
  }
}

class UserService {
  constructor(db) {
    this.db = db;
  }

  async getUser(id) {
    const data = await this.db.query('users', { where: { id } });
    return data ? new User(data.id, data.name, data.email) : null;
  }

  async createUser(user) {
    await this.db.insert('users', user);
    return user;
  }
}

const createSession = (user) => {
  const session = new Session(user.id);
  session.save();
  return session;
};

class Session {
  constructor(userId) {
    this.userId = userId;
    this.createdAt = new Date();
  }

  get isValid() {
    const hours = (Date.now() - this.createdAt.getTime()) / (1000 * 60 * 60);
    return hours < 24;
  }

  save() {
    // 保存会话
  }

  static async fromUserId(userId) {
    const session = new Session(userId);
    await session.save();
    return session;
  }
}

// 箭头函数示例
const fetchUser = async (id) => {
  const response = await fetch(`/api/users/${id}`);
  return await response.json();
};

// 对象解构示例
const { id, name } = await fetchUser(1);
