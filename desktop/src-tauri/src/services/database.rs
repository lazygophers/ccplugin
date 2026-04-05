use rusqlite::Connection;
use std::path::PathBuf;

/// 数据库路径：~/.lazygophers/ccplugin/desktop/notifications.db
pub fn get_database_path() -> Result<PathBuf, String> {
    let home = dirs::home_dir()
        .ok_or("Failed to get home directory")?;

    let db_dir = home.join(".lazygophers/ccplugin/desktop");

    // 确保目录存在
    std::fs::create_dir_all(&db_dir)
        .map_err(|e| format!("Failed to create database directory: {}", e))?;

    Ok(db_dir.join("notifications.db"))
}

/// 初始化数据库连接并创建表
pub fn init_database() -> Result<Connection, String> {
    let db_path = get_database_path()?;

    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;

    // 创建通知表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            read INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            metadata TEXT
        )",
        [],
    )
    .map_err(|e| format!("Failed to create notifications table: {}", e))?;

    // 创建索引：按 updated_at 倒序查询优化
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_updated_at
         ON notifications(updated_at DESC)",
        [],
    )
    .map_err(|e| format!("Failed to create index on updated_at: {}", e))?;

    // 创建索引：按 read 状态查询优化
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_read
         ON notifications(read)",
        [],
    )
    .map_err(|e| format!("Failed to create index on read: {}", e))?;

    Ok(conn)
}

/// 获取数据库连接（每次调用新建连接）
pub fn get_connection() -> Result<Connection, String> {
    let db_path = get_database_path()?;

    // 如果数据库文件不存在，初始化它
    if !db_path.exists() {
        return init_database();
    }

    Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))
}
