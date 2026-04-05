use crate::models::Notification;
use crate::services::database::{get_connection, init_database};
use rusqlite::{params, Row};
use std::sync::Mutex;
use tauri::AppHandle;

pub struct NotificationService;

impl NotificationService {
    pub fn new(_app_handle: &AppHandle) -> Result<Self, String> {
        // 初始化数据库
        init_database()?;

        Ok(Self)
    }

    /// 添加通知
    pub fn add_notification(&self, notification: &Notification) -> Result<(), String> {
        let conn = get_connection()?;

        let metadata_json = serde_json::to_string(&notification.metadata)
            .map_err(|e| format!("Failed to serialize metadata: {}", e))?;

        conn.execute(
            "INSERT INTO notifications (id, type, title, message, read, created_at, updated_at, metadata)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![
                notification.id,
                serde_json::to_string(&notification.notification_type)
                    .map_err(|e| format!("Failed to serialize type: {}", e))?,
                notification.title,
                notification.message,
                notification.read as i32,
                notification.created_at,
                notification.updated_at,
                metadata_json,
            ],
        )
        .map_err(|e| format!("Failed to insert notification: {}", e))?;

        Ok(())
    }

    /// 获取所有通知（按 updated_at 倒序）
    pub fn get_notifications(&self) -> Result<Vec<Notification>, String> {
        let conn = get_connection()?;

        let mut stmt = conn
            .prepare(
                "SELECT id, type, title, message, read, created_at, updated_at, metadata
                 FROM notifications
                 ORDER BY updated_at DESC",
            )
            .map_err(|e| format!("Failed to prepare statement: {}", e))?;

        let notifications = stmt
            .query_map([], |row| Self::row_to_notification(row))
            .map_err(|e| format!("Failed to query notifications: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to parse notification: {}", e))?;

        Ok(notifications)
    }

    /// 获取未读数量
    pub fn get_unread_count(&self) -> Result<usize, String> {
        let conn = get_connection()?;

        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM notifications WHERE read = 0",
                [],
                |row| row.get(0),
            )
            .map_err(|e| format!("Failed to count unread: {}", e))?;

        Ok(count as usize)
    }

    /// 标记为已读
    pub fn mark_as_read(&self, id: &str) -> Result<Option<Notification>, String> {
        let conn = get_connection()?;

        // 先获取原通知
        let notification = conn
            .query_row(
                "SELECT id, type, title, message, read, created_at, updated_at, metadata
                 FROM notifications WHERE id = ?1",
                [id],
                |row| Self::row_to_notification(row),
            );

        match notification {
            Ok(notif) => {
                // 更新为已读
                let updated_at = chrono::Utc::now().timestamp();
                conn.execute(
                    "UPDATE notifications SET read = 1, updated_at = ?1 WHERE id = ?2",
                    params![updated_at, id],
                )
                .map_err(|e| format!("Failed to mark as read: {}", e))?;

                Ok(Some(notif))
            }
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(format!("Failed to query notification: {}", e)),
        }
    }

    /// 标记所有为已读
    pub fn mark_all_as_read(&self) -> Result<(), String> {
        let conn = get_connection()?;

        let updated_at = chrono::Utc::now().timestamp();
        conn.execute(
            "UPDATE notifications SET read = 1, updated_at = ?1 WHERE read = 0",
            params![updated_at],
        )
        .map_err(|e| format!("Failed to mark all as read: {}", e))?;

        Ok(())
    }

    /// 更新通知消息
    pub fn update_notification(&self, id: &str, message: String) -> Result<Option<Notification>, String> {
        let conn = get_connection()?;

        // 检查通知是否存在
        let exists: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM notifications WHERE id = ?1",
                [id],
                |row| row.get(0),
            )
            .map_err(|e| format!("Failed to check notification: {}", e))?;

        if exists == 0 {
            return Ok(None);
        }

        // 更新消息和时间戳
        let updated_at = chrono::Utc::now().timestamp();
        conn.execute(
            "UPDATE notifications SET message = ?1, updated_at = ?2 WHERE id = ?3",
            params![message, updated_at, id],
        )
        .map_err(|e| format!("Failed to update notification: {}", e))?;

        // 返回更新后的通知
        let notification = conn
            .query_row(
                "SELECT id, type, title, message, read, created_at, updated_at, metadata
                 FROM notifications WHERE id = ?1",
                [id],
                |row| Self::row_to_notification(row),
            )
            .map_err(|e| format!("Failed to query updated notification: {}", e))?;

        Ok(Some(notification))
    }

    /// 删除通知
    pub fn delete_notification(&self, id: &str) -> Result<bool, String> {
        let conn = get_connection()?;

        let rows_affected = conn
            .execute("DELETE FROM notifications WHERE id = ?1", [id])
            .map_err(|e| format!("Failed to delete notification: {}", e))?;

        Ok(rows_affected > 0)
    }

    /// 清空所有通知
    pub fn clear_all(&self) -> Result<(), String> {
        let conn = get_connection()?;

        conn.execute("DELETE FROM notifications", [])
            .map_err(|e| format!("Failed to clear notifications: {}", e))?;

        Ok(())
    }

    /// 根据元数据查找通知（用于异步任务进度更新）
    pub fn find_by_metadata(
        &self,
        key: &str,
        value: &serde_json::Value,
    ) -> Result<Option<Notification>, String> {
        let conn = get_connection()?;

        let metadata_json = serde_json::to_string(value)
            .map_err(|e| format!("Failed to serialize value: {}", e))?;

        // 使用 JSON 查询：metadata 中包含指定 key-value 对
        let pattern = format!("\"{}\":{}", key, metadata_json);

        let notification = conn
            .query_row(
                "SELECT id, type, title, message, read, created_at, updated_at, metadata
                 FROM notifications
                 WHERE metadata LIKE ?1
                 LIMIT 1",
                [&pattern],
                |row| Self::row_to_notification(row),
            );

        match notification {
            Ok(n) => Ok(Some(n)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(format!("Failed to find notification: {}", e)),
        }
    }

    /// 辅助方法：将数据库行转换为 Notification
    fn row_to_notification(row: &Row) -> rusqlite::Result<Notification> {
        let type_str: String = row.get(1)?;
        let notification_type = serde_json::from_str(&type_str)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;

        let metadata_str: Option<String> = row.get(7)?;
        let metadata = metadata_str
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();

        Ok(Notification {
            id: row.get(0)?,
            notification_type,
            title: row.get(2)?,
            message: row.get(3)?,
            read: row.get::<_, i32>(4)? != 0,
            created_at: row.get(5)?,
            updated_at: row.get(6)?,
            metadata,
        })
    }
}

// 全局单例（使用 Mutex 包装以支持可变访问）
use std::sync::OnceLock;

static NOTIFICATION_SERVICE: OnceLock<Mutex<NotificationService>> = OnceLock::new;

pub fn init_notification_service(app_handle: &AppHandle) -> Result<(), String> {
    let service = NotificationService::new(app_handle)?;
    NOTIFICATION_SERVICE
        .set(Mutex::new(service))
        .map_err(|_| "Notification service already initialized".to_string())?;
    Ok(())
}

pub fn notification_service() -> Option<&'static Mutex<NotificationService>> {
    NOTIFICATION_SERVICE.get()
}

pub fn notification_service_mut() -> Option<&'static Mutex<NotificationService>> {
    NOTIFICATION_SERVICE.get()
}
