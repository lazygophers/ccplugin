// Flutter/Dart 测试文件 - 包含类、方法、异步函数

class User {
  final int id;
  final String name;
  final String email;
  final DateTime createdAt;

  User({
    required this.id,
    required this.name,
    required this.email,
  }) : createdAt = DateTime.now();

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      name: json['name'],
      email: json['email'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  Future<bool> authenticate(String password) async {
    return await _checkPassword(password);
  }

  Future<bool> _checkPassword(String password) async {
    return password.isNotEmpty;
  }
}

abstract class UserService {
  Future<User?> getUser(int id);
  Future<void> createUser(User user);
}

class UserServiceImpl extends UserService {
  final Database _db;

  UserServiceImpl(this._db);

  @override
  Future<User?> getUser(int id) async {
    final data = await _db.query('users', where: 'id = ?', whereArgs: [id]);
    if (data.isEmpty) return null;
    return User.fromJson(data.first);
  }

  @override
  Future<void> createUser(User user) async {
    await _db.insert('users', user.toJson());
  }
}

class Session {
  final int userId;
  final DateTime createdAt;

  Session(this.userId) : createdAt = DateTime.now();

  factory Session.fromUserId(int userId) {
    return Session(userId);
  }

  bool get isValid {
    return DateTime.now().difference(createdAt) < Duration(hours: 24);
  }

  Future<void> save() async {
    // 保存会话
  }
}

Future<Session> createSession(User user) async {
  final session = Session.fromUserId(user.id);
  await session.save();
  return session;
}
