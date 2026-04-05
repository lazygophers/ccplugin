use crate::models::{Notification, NotificationType};
use crate::services::notification_service_mut;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::{AppHandle, Emitter};

/// 插件事件负载
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginEventPayload {
    pub event_type: String,
    pub plugin_name: String,
    pub data: Value,
}

/// 插件事件类型
pub enum PluginEventType {
    // 安装事件
    PluginInstallStarted,
    PluginInstallProgress,
    PluginInstallCompleted,
    PluginInstallFailed,

    // 更新事件
    PluginUpdateStarted,
    PluginUpdateProgress,
    PluginUpdateCompleted,
    PluginUpdateFailed,

    // 卸载事件
    PluginUninstallStarted,
    PluginUninstallProgress,
    PluginUninstallCompleted,
    PluginUninstallFailed,

    // 缓存清理事件
    CacheCleanStarted,
    CacheCleanCompleted,
    CacheCleanFailed,

    // 插件信息获取事件
    PluginInfoCompleted,
    PluginInfoFailed,
}

impl PluginEventType {
    /// 转换为事件名称字符串（遵循 <domain>-<entity>-<action> 格式）
    pub fn as_str(&self) -> &'static str {
        match self {
            PluginEventType::PluginInstallStarted => "plugin-install-started",
            PluginEventType::PluginInstallProgress => "plugin-install-progress",
            PluginEventType::PluginInstallCompleted => "plugin-install-completed",
            PluginEventType::PluginInstallFailed => "plugin-install-failed",

            PluginEventType::PluginUpdateStarted => "plugin-update-started",
            PluginEventType::PluginUpdateProgress => "plugin-update-progress",
            PluginEventType::PluginUpdateCompleted => "plugin-update-completed",
            PluginEventType::PluginUpdateFailed => "plugin-update-failed",

            PluginEventType::PluginUninstallStarted => "plugin-uninstall-started",
            PluginEventType::PluginUninstallProgress => "plugin-uninstall-progress",
            PluginEventType::PluginUninstallCompleted => "plugin-uninstall-completed",
            PluginEventType::PluginUninstallFailed => "plugin-uninstall-failed",

            PluginEventType::CacheCleanStarted => "cache-clean-started",
            PluginEventType::CacheCleanCompleted => "cache-clean-completed",
            PluginEventType::CacheCleanFailed => "cache-clean-failed",

            PluginEventType::PluginInfoCompleted => "plugin-info-completed",
            PluginEventType::PluginInfoFailed => "plugin-info-failed",
        }
    }
}

/// 发送插件事件到前端
pub fn emit_plugin_event(
    app_handle: &AppHandle,
    event_type: PluginEventType,
    plugin_name: &str,
    data: Value,
) {
    let payload = PluginEventPayload {
        event_type: event_type.as_str().to_string(),
        plugin_name: plugin_name.to_string(),
        data: data.clone(),
    };

    let _ = app_handle.emit("plugin-event", Some(payload));

    // 同时添加到通知中心
    add_notification_for_event(app_handle, &event_type, plugin_name, &data);
}

/// 根据事件类型创建通知
fn add_notification_for_event(
    _app_handle: &AppHandle,
    event_type: &PluginEventType,
    plugin_name: &str,
    data: &Value,
) {
    let (notif_type, title, message) = match event_type {
        PluginEventType::PluginInstallStarted => {
            (NotificationType::Info, "开始安装", format!("正在安装 {}", plugin_name))
        }
        PluginEventType::PluginInstallProgress => {
            let progress = data.get("progress").and_then(|v| v.as_u64()).unwrap_or(0);
            let msg = data.get("message").and_then(|v| v.as_str()).unwrap_or("处理中...");
            (
                NotificationType::Progress,
                "安装进度",
                format!("{}: {}% - {}", plugin_name, progress, msg),
            )
        }
        PluginEventType::PluginInstallCompleted => {
            (NotificationType::Success, "安装完成", format!("{} 已成功安装", plugin_name))
        }
        PluginEventType::PluginInstallFailed => {
            let error = data.get("error").and_then(|v| v.as_str()).unwrap_or("未知错误");
            (NotificationType::Error, "安装失败", format!("{}: {}", plugin_name, error))
        }
        PluginEventType::PluginUpdateStarted => {
            (NotificationType::Info, "开始更新", format!("正在更新 {}", plugin_name))
        }
        PluginEventType::PluginUpdateProgress => {
            let progress = data.get("progress").and_then(|v| v.as_u64()).unwrap_or(0);
            let msg = data.get("message").and_then(|v| v.as_str()).unwrap_or("处理中...");
            (
                NotificationType::Progress,
                "更新进度",
                format!("{}: {}% - {}", plugin_name, progress, msg),
            )
        }
        PluginEventType::PluginUpdateCompleted => {
            (NotificationType::Success, "更新完成", format!("{} 已成功更新", plugin_name))
        }
        PluginEventType::PluginUpdateFailed => {
            let error = data.get("error").and_then(|v| v.as_str()).unwrap_or("未知错误");
            (NotificationType::Error, "更新失败", format!("{}: {}", plugin_name, error))
        }
        PluginEventType::PluginUninstallStarted => {
            (NotificationType::Info, "开始卸载", format!("正在卸载 {}", plugin_name))
        }
        PluginEventType::PluginUninstallProgress => {
            let msg = data.get("message").and_then(|v| v.as_str()).unwrap_or("处理中...");
            (NotificationType::Progress, "卸载进度", format!("{}: {}", plugin_name, msg))
        }
        PluginEventType::PluginUninstallCompleted => {
            (NotificationType::Success, "卸载完成", format!("{} 已成功卸载", plugin_name))
        }
        PluginEventType::PluginUninstallFailed => {
            let error = data.get("error").and_then(|v| v.as_str()).unwrap_or("未知错误");
            (NotificationType::Error, "卸载失败", format!("{}: {}", plugin_name, error))
        }
        PluginEventType::CacheCleanStarted => {
            (NotificationType::Info, "清理缓存", "正在清理缓存...".to_string())
        }
        PluginEventType::CacheCleanCompleted => {
            (NotificationType::Success, "清理完成", "缓存已成功清理".to_string())
        }
        PluginEventType::CacheCleanFailed => {
            let error = data.get("error").and_then(|v| v.as_str()).unwrap_or("未知错误");
            (NotificationType::Error, "清理失败", format!("缓存清理失败: {}", error))
        }
        PluginEventType::PluginInfoCompleted => {
            // 信息获取事件不创建通知
            return;
        }
        PluginEventType::PluginInfoFailed => {
            // 信息获取失败不创建通知
            return;
        }
    };

    // 创建通知
    let mut notification = Notification::new(notif_type, title.to_string(), message);

    // 添加元数据用于关联和更新
    let event_name = event_type.as_str();
    notification = notification
        .with_metadata("event".to_string(), Value::String(event_name.to_string()))
        .with_metadata("plugin".to_string(), Value::String(plugin_name.to_string()));

    // 对于进度事件，添加特殊标记用于更新而非新建
    if matches!(
        event_type,
        PluginEventType::PluginInstallProgress
            | PluginEventType::PluginUpdateProgress
            | PluginEventType::PluginUninstallProgress
    ) {
        notification = notification.with_metadata(
            "progress_key".to_string(),
            Value::String(format!("{}-{}", event_name, plugin_name)),
        );

        // 尝试更新现有进度通知
        if let Some(mutex) = notification_service_mut() {
            if let Ok(service) = mutex.lock() {
                let progress_key = Value::String(format!("{}-{}", event_name, plugin_name));
                if let Ok(Some(existing)) = service.find_by_metadata("progress_key", &progress_key) {
                    let _ = service.update_notification(&existing.id, notification.message.clone());
                    return;
                }
            }
        }
    }

    // 添加通知
    if let Some(mutex) = notification_service_mut() {
        if let Ok(service) = mutex.lock() {
            let _ = service.add_notification(&notification);
        }
    }
}
