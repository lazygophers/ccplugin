// Swift 测试文件 - 包含类、结构体、协议、扩展

import Foundation

struct User: Codable {
    let id: Int
    let name: String
    let email: String
    let createdAt: Date

    init(id: Int, name: String, email: String) {
        self.id = id
        self.name = name
        self.email = email
        self.createdAt = Date()
    }

    func authenticate(password: String) -> Bool {
        return checkPassword(password)
    }

    private func checkPassword(password: String) -> Bool {
        return !password.isEmpty
    }
}

protocol UserService {
    func getUser(id: Int) async throws -> User
    func createUser(user: User) async throws
}

class UserServiceImpl: UserService {
    private let db: Database

    init(db: Database) {
        self.db = db
    }

    func getUser(id: Int) async throws -> User {
        let data = try await db.query("users", where: ["id": id])
        guard let data = data else {
            throw UserServiceError.notFound
        }
        return User(id: data["id"] as! Int, name: data["name"] as! String, email: data["email"] as! String)
    }

    func createUser(user: User) async throws {
        try await db.insert("users", user)
    }
}

enum UserServiceError: Error {
    case notFound
    case invalidInput
}

class Session {
    let userId: Int
    let createdAt: Date

    init(userId: Int) {
        self.userId = userId
        self.createdAt = Date()
    }

    var isValid: Bool {
        let hours = Date().timeIntervalSince(createdAt) / 3600
        return hours < 24
    }

    func save() {
        // 保存会话
    }
}

extension Session {
    static func create(userId: Int) -> Session {
        let session = Session(userId: userId)
        session.save()
        return session
    }
}
