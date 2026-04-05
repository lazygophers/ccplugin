use crate::models::{Notification, NotificationType};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use tauri::AppHandle;

pub struct NotificationService {
    notifications: Vec<Notification>,
    file_path: PathBuf,
}

impl NotificationService {
    pub fn new(app_handle: &AppHandle) -> Result<Self, String> {
        let app_local_data_dir = app_handle
            .path()
            .app_local_data_dir()
            .map_err(|e| format!("Failed to get app local data dir: {}", e))?;

        let file_path = app_local_data_dir.join("notifications.json");

        let notifications = if file_path.exists() {
            Self::load_from_file(&file_path)?
        } else {
            Vec::new()
        };

        Ok(Self {
            notifications,
            file_path,
        })
    }

    fn load_from_file(path: &PathBuf) -> Result<Vec<Notification>, String> {
        let content = fs::read_to_string(path)
            .map_err(|e| format!("Failed to read notifications: {}", e))?;

        serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse notifications: {}", e))
    }

    fn save_to_file(&self) -> Result<(), String> {
        let json = serde_json::to_string_pretty(&self.notifications)
            .map_err(|e| format!("Failed to serialize notifications: {}", e))?;

        fs::write(&self.file_path, json)
            .map_err(|e| format!("Failed to write notifications: {}", e))?;

        Ok(())
    }

    pub fn add_notification(&mut self, notification: Notification) -> Result<Notification, String> {
        self.notifications.push(notification.clone());
        self.save_to_file()?;
        Ok(notification)
    }

    pub fn get_notifications(&self) -> Vec<Notification> {
        // 按 updated_at 倒序排列
        let mut notifications = self.notifications.clone();
        notifications.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
        notifications
    }

    pub fn get_unread_count(&self) -> usize {
        self.notifications.iter().filter(|n| !n.read).count()
    }

    pub fn mark_as_read(&mut self, id: &str) -> Result<Option<Notification>, String> {
        if let Some(notification) = self.notifications.iter_mut().find(|n| n.id == id) {
            notification.mark_read();
            self.save_to_file()?;
            Ok(Some(notification.clone()))
        } else {
            Ok(None)
        }
    }

    pub fn mark_all_as_read(&mut self) -> Result<(), String> {
        for notification in &mut self.notifications {
            if !notification.read {
                notification.mark_read();
            }
        }
        self.save_to_file()?;
        Ok(())
    }

    pub fn update_notification(
        &mut self,
        id: &str,
        message: String,
    ) -> Result<Option<Notification>, String> {
        if let Some(notification) = self.notifications.iter_mut().find(|n| n.id == id) {
            notification.update_message(message);
            self.save_to_file()?;
            Ok(Some(notification.clone()))
        } else {
            Ok(None)
        }
    }

    pub fn delete_notification(&mut self, id: &str) -> Result<bool, String> {
        let initial_len = self.notifications.len();
        self.notifications.retain(|n| n.id != id);

        if self.notifications.len() < initial_len {
            self.save_to_file()?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn clear_all(&mut self) -> Result<(), String> {
        self.notifications.clear();
        self.save_to_file()?;
        Ok(())
    }

    /// 根据元数据查找通知（用于异步任务进度更新）
    pub fn find_by_metadata(
        &self,
        key: &str,
        value: &serde_json::Value,
    ) -> Option<&Notification> {
        self.notifications
            .iter()
            .find(|n| n.metadata.get(key) == Some(value))
    }

    pub fn find_by_metadata_mut(
        &mut self,
        key: &str,
        value: &serde_json::Value,
    ) -> Option<&mut Notification> {
        self.notifications
            .iter_mut()
            .find(|n| n.metadata.get(key) == Some(value))
    }
}

// 全局单例（使用 Once Lock）
use std::sync::OnceLock;

static NOTIFICATION_SERVICE: OnceLock<NotificationService> = OnceLock::new;

pub fn init_notification_service(app_handle: &AppHandle) -> Result<(), String> {
    let service = NotificationService::new(app_handle)?;
    NOTIFICATION_SERVICE
        .set(service)
        .map_err(|_| "Notification service already initialized".to_string())?;
    Ok(())
}

pub fn notification_service() -> Option<&'static NotificationService> {
    NOTIFICATION_SERVICE.get()
}

pub fn notification_service_mut() -> Option<&'static mut NotificationService> {
    unsafe {
        // SAFETY: 我们只在初始化后调用，且保证单例
        NOTIFICATION_SERVICE.get_mut()
    }
}
