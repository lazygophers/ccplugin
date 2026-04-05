use crate::models::CommandResult;
use crate::services::PythonBridge;
use tauri::{AppHandle, State};
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct PythonBridgeState(pub Arc<Mutex<Option<PythonBridge>>>);

#[tauri::command]
pub async fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    let bridge = bridge_guard.as_ref().unwrap();
    let scope = scope.unwrap_or_else(|| "user".to_string());
    bridge.install_plugin(&plugin_name, &marketplace, &scope).await
}

#[tauri::command]
pub async fn update_plugin(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    let bridge = bridge_guard.as_ref().unwrap();
    bridge.update_plugin(&plugin_name).await
}

#[tauri::command]
pub async fn uninstall_plugin(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    let bridge = bridge_guard.as_ref().unwrap();
    bridge.uninstall_plugin(&plugin_name).await
}

#[tauri::command]
pub async fn clean_cache(
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    let bridge = bridge_guard.as_ref().unwrap();
    bridge.clean_cache().await
}

#[tauri::command]
pub async fn get_plugin_info(
    plugin_name: String,
    app_handle: AppHandle,
    state: State<'_, PythonBridgeState>,
) -> Result<CommandResult, String> {
    let mut bridge_guard = state.0.lock().await;
    if bridge_guard.is_none() {
        *bridge_guard = Some(PythonBridge::new(app_handle));
    }
    let bridge = bridge_guard.as_ref().unwrap();
    bridge.get_plugin_info(&plugin_name).await
}
