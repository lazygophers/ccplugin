// Java 测试文件 - 包含类、接口、注解

import java.util.*;
import java.time.DateTime;

public class User {
    private int id;
    private String name;
    private String email;
    private DateTime createdAt;

    @Override
    public String toString() {
        return "User{id=" + id + ", name='" + name + "'}";
    }

    public User(int id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.createdAt = DateTime.now();
    }

    public boolean authenticate(String password) {
        return checkPassword(password);
    }

    private boolean checkPassword(String password) {
        return password != null && !password.isEmpty();
    }

    public int getId() {
        return id;
    }

    public String getName() {
        return name;
    }
}

interface UserService {
    User getUser(int id) throws UserNotFoundException;
    void createUser(User user);
}

class UserServiceImpl implements UserService {
    private Database db;

    public UserServiceImpl(Database db) {
        this.db = db;
    }

    @Override
    public User getUser(int id) throws UserNotFoundException {
        // 实现逻辑
        return new User(id, "Test", "test@example.com");
    }

    @Override
    public void createUser(User user) {
        // 实现逻辑
    }
}

class Session {
    private int userId;
    private DateTime createdAt;

    public Session(int userId) {
        this.userId = userId;
        this.createdAt = DateTime.now();
    }

    public boolean isValid() {
        return DateTime.now().difference(createdAt).toHours() < 24;
    }

    public void save() {
        // 保存会话
    }
}

public class SessionFactory {
    public static Session createSession(User user) {
        Session session = new Session(user.getId());
        session.save();
        return session;
    }
}
