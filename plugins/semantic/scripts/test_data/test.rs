// Rust 测试文件 - 包含结构体、trait、impl、函数

struct User {
    id: u64,
    name: String,
    email: String,
}

impl User {
    fn new(id: u64, name: String, email: String) -> Self {
        Self { id, name, email }
    }

    fn authenticate(&self, password: &str) -> bool {
        self.check_password(password)
    }

    fn check_password(&self, password: &str) -> bool {
        !password.is_empty()
    }
}

trait UserService {
    fn get_user(&self, id: u64) -> Option<User>;
    fn create_user(&mut self, user: User) -> Result<(), Error>;
}

struct UserServiceImpl {
    users: Vec<User>,
}

impl UserService for UserServiceImpl {
    fn get_user(&self, id: u64) -> Option<User> {
        self.users.iter().find(|u| u.id == id).cloned()
    }

    fn create_user(&mut self, user: User) -> Result<(), Error> {
        self.users.push(user);
        Ok(())
    }
}

#[derive(Debug)]
enum Error {
    NotFound,
    InvalidInput,
}

pub async fn fetch_user(id: u64) -> Result<User, Error> {
    // 异步获取用户
    Err(Error::NotFound)
}

pub fn create_session(user: &User) -> Session {
    Session::new(user.id)
}

struct Session {
    user_id: u64,
    created_at: std::time::Instant,
}

impl Session {
    fn new(user_id: u64) -> Self {
        Self {
            user_id,
            created_at: std::time::Instant::now(),
        }
    }

    fn is_valid(&self) -> bool {
        self.created_at.elapsed() < std::time::Duration::from_secs(86400)
    }
}
