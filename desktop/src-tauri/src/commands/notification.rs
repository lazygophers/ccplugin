use crate::models::{Notification, NotificationType};
use crate::services::notification_service_mut;
use serde_json::Value;
use tauri::AppHandle;

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

    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    service.add_notification(notification.clone())
}

#[tauri::command]
pub fn get_notifications() -> Result<Vec<Notification>, String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    Ok(service.get_notifications())
}

#[tauri::command]
pub fn get_unread_count() -> Result<usize, String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    Ok(service.get_unread_count())
}

#[tauri::command]
pub fn mark_notification_read(id: String) -> Result<bool, String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    Ok(service.mark_as_read(&id)?.is_some())
}

#[tauri::command]
pub fn mark_all_notifications_read() -> Result<(), String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    service.mark_all_as_read()
}

#[tauri::command]
pub fn update_notification(id: String, message: String) -> Result<bool, String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    Ok(service.update_notification(&id, message)?.is_some())
}

#[tauri::command]
pub fn delete_notification(id: String) -> Result<bool, String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    service.delete_notification(&id)
}

#[tauri::command]
pub fn clear_all_notifications() -> Result<(), String> {
    let service = notification_service_mut()
        .ok_or("Notification service not initialized")?;

    service.clear_all()
}
