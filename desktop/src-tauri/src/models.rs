use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Python命令执行结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

/// 插件安装状态
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum InstallStatus {
    Downloading,
    Installing,
    Completed,
    Failed,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_result_serialization() {
        let result = CommandResult {
            success: true,
            stdout: "test output".to_string(),
            stderr: "".to_string(),
        };

        let json = serde_json::to_string(&result).unwrap();
        assert!(json.contains("\"success\":true"));
        assert!(json.contains("test output"));
    }

    #[test]
    fn test_install_status_serialization() {
        let status = InstallStatus::Downloading;
        let json = serde_json::to_string(&status).unwrap();
        assert_eq!(json, "\"downloading\"");
    }
}

/// 通知模型
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Notification {
    pub id: String,
    #[serde(rename = "type")]
    pub notification_type: NotificationType,
    pub title: String,
    pub message: String,
    pub read: bool,
    pub created_at: i64,
    #[serde(default)]
    pub updated_at: i64,
    #[serde(default)]
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum NotificationType {
    Info,
    Success,
    Warning,
    Error,
    Progress,
}

impl Notification {
    pub fn new(
        notification_type: NotificationType,
        title: String,
        message: String,
    ) -> Self {
        let now = chrono::Utc::now().timestamp();
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            notification_type,
            title,
            message,
            read: false,
            created_at: now,
            updated_at: now,
            metadata: HashMap::new(),
        }
    }

    pub fn with_metadata(mut self, key: String, value: serde_json::Value) -> Self {
        self.metadata.insert(key, value);
        self
    }

    pub fn mark_read(&mut self) -> &mut Self {
        self.read = true;
        self.updated_at = chrono::Utc::now().timestamp();
        self
    }

    pub fn update_message(&mut self, message: String) -> &mut Self {
        self.message = message;
        self.updated_at = chrono::Utc::now().timestamp();
        self
    }
}

#[cfg(test)]
mod notification_tests {
    use super::*;

    #[test]
    fn test_notification_creation() {
        let notification = Notification::new(
            NotificationType::Info,
            "Test".to_string(),
            "Test message".to_string(),
        );

        assert!(!notification.read);
        assert_eq!(notification.title, "Test");
    }

    #[test]
    fn test_notification_mark_read() {
        let mut notification = Notification::new(
            NotificationType::Success,
            "Test".to_string(),
            "Test message".to_string(),
        );

        notification.mark_read();
        assert!(notification.read);
    }

    #[test]
    fn test_notification_update_message() {
        let mut notification = Notification::new(
            NotificationType::Progress,
            "Test".to_string(),
            "Old message".to_string(),
        );

        let old_updated = notification.updated_at;
        notification.update_message("New message".to_string());

        assert_eq!(notification.message, "New message");
        assert!(notification.updated_at > old_updated);
    }
}
