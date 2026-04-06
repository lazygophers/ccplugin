use crate::models::{Notification, NotificationType};
use crate::services::notification_service_mut;
use serde_json::Value;
use tauri::{AppHandle, Emitter};
use tauri_plugin_notification::NotificationExt;

#[tauri::command]
pub fn add_notification(
    notification_type: String,
    title: String,
    message: String,
    metadata: Option<Value>,
) -> Result<Notification, String> {
    let notif_type = match notification_type.as_str() {
        "info" => NotificationType::Info,
        "success" => NotificationType::Success,
        "warning" => NotificationType::Warning,
        "error" => NotificationType::Error,
        "progress" => NotificationType::Progress,
        _ => NotificationType::Info,
    };

    let mut notification = Notification::new(notif_type, title, message);

    if let Some(meta) = metadata {
        if let Some(obj) = meta.as_object() {
            for (key, value) in obj {
                notification = notification.with_metadata(key.clone(), value.clone());
            }
        }
    }

    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.add_notification(&notification)?;
    Ok(notification)
}

#[tauri::command]
pub fn get_notifications() -> Result<Vec<Notification>, String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.get_notifications()
}

#[tauri::command]
pub fn get_unread_count() -> Result<usize, String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.get_unread_count()
}

#[tauri::command]
pub fn mark_notification_read(id: String) -> Result<bool, String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    Ok(service.mark_as_read(&id)?.is_some())
}

#[tauri::command]
pub fn mark_all_notifications_read() -> Result<(), String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.mark_all_as_read()
}

#[tauri::command]
pub fn update_notification(id: String, message: String) -> Result<bool, String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    Ok(service.update_notification(&id, message)?.is_some())
}

#[tauri::command]
pub fn delete_notification(id: String) -> Result<bool, String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.delete_notification(&id)
}

#[tauri::command]
pub fn clear_all_notifications() -> Result<(), String> {
    let mutex = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    let service = mutex.lock().map_err(|e| format!("Failed to lock service: {}", e))?;
    service.clear_all()
}

/// 发送系统通知（右下角弹窗）
#[tauri::command]
pub fn send_system_notification(
    title: String,
    body: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let _ = app_handle
        .notification()
        .builder()
        .title(title)
        .body(body)
        .show();

    Ok(())
}

