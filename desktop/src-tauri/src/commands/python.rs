use crate::models::CommandResult;
use crate::services::PythonBridge;
use tauri::{AppHandle, State};
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct PythonBridgeState(pub Arc<Mutex<Option<PythonBridge>>>);

/// 获取或初始化 PythonBridge 实例
async fn get_bridge(
    state: State<'_, PythonBridgeState>,
    app_handle: AppHandle,
) -> Result<PythonBridge, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    // 由于 PythonBridge 只包含 AppHandle，可以 clone
    bridge_guard
        .as_ref()
        .ok_or_else(|| "Failed to initialize PythonBridge".to_string())
        .map(|bridge| PythonBridge::new(bridge.app_handle.clone()))
}

#[tauri::command]
pub async fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let bridge = get_bridge(state, app_handle).await?;
    let scope = scope.unwrap_or_else(|| "user".to_string());
    bridge.install_plugin(&plugin_name, &marketplace, &scope).await
}

#[tauri::command]
pub async fn update_plugin(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let bridge = get_bridge(state, app_handle).await?;
    bridge.update_plugin(&plugin_name).await
}

#[tauri::command]
pub async fn uninstall_plugin(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let bridge = get_bridge(state, app_handle).await?;
    bridge.uninstall_plugin(&plugin_name).await
}

#[tauri::command]
pub async fn clean_cache(
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let bridge = get_bridge(state, app_handle).await?;
    bridge.clean_cache().await
}

#[tauri::command]
pub async fn get_plugin_info(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let bridge = get_bridge(state, app_handle).await?;
    bridge.get_plugin_info(&plugin_name).await
}
