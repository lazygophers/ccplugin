use crate::services::task_queue::{Task, TaskType};
use tauri::AppHandle;

#[tauri::command]
pub fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    _app_handle: AppHandle,
) -> Result<(), String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    let task = Task::new(
        TaskType::Install,
        plugin_name,
        Some(marketplace),
        scope,
    );

    task_queue.add_task(task)?;
    Ok(())
}

#[tauri::command]
pub fn uninstall_plugin(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    let task = Task::new(
        TaskType::Uninstall,
        plugin_name,
        None,
        None,
    );

    task_queue.add_task(task)?;
    Ok(())
}

#[tauri::command]
pub fn update_plugin(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    let task = Task::new(
        TaskType::Update,
        plugin_name,
        None,
        None,
    );

    task_queue.add_task(task)?;
    Ok(())
}

#[tauri::command]
pub fn get_tasks() -> Result<Vec<Task>, String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    task_queue.get_all_tasks()
}

#[tauri::command]
pub fn get_task_status() -> Result<crate::services::TaskQueueStatus, String> {
    let task_queue = crate::services::task_queue()
        .ok_or("任务队列未初始化".to_string())?;

    task_queue.get_status()
}
