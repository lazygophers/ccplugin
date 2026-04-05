use crate::events::{emit_plugin_event, PluginEventType};
use crate::services::PythonBridge;
use serde_json::json;
use tauri::AppHandle;

#[tauri::command]
pub fn install_plugin(
    plugin_name: String,
    marketplace: String,
    scope: Option<String>,
    app_handle: AppHandle,
) -> Result<(), String> {
    let bridge = PythonBridge::new();
    let plugin_name_clone = plugin_name.clone();
    let app_handle_clone = app_handle.clone();
    let marketplace_clone = marketplace.clone();
    let scope_value = scope.unwrap_or_else(|| "user".to_string());

    // Spawn background task
    tokio::spawn(async move {
        // Emit started event
        emit_plugin_event(
            &app_handle_clone,
            PluginEventType::PluginInstallStarted,
            &plugin_name_clone,
            json!({ "marketplace": marketplace_clone, "scope": scope_value }),
        );

        // Execute installation
        let result = bridge
            .install_plugin_with_progress(
                &plugin_name_clone,
                &marketplace_clone,
                &scope_value,
                |status, progress, message| {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginInstallProgress,
                        &plugin_name_clone,
                        json!({
                            "status": status,
                            "progress": progress,
                            "message": message
                        }),
                    );
                },
            )
            .await;

        // Emit completion event
        match result {
            Ok(result) => {
                if result.success {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginInstallCompleted,
                        &plugin_name_clone,
                        json!({
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        }),
                    );
                } else {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginInstallFailed,
                        &plugin_name_clone,
                        json!({
                            "error": result.stderr,
                        }),
                    );
                }
            }
            Err(err) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::PluginInstallFailed,
                    &plugin_name_clone,
                    json!({
                        "error": err,
                    }),
                );
            }
        }
    });

    // Return immediately
    Ok(())
}

#[tauri::command]
pub fn update_plugin(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let bridge = PythonBridge::new();
    let plugin_name_clone = plugin_name.clone();
    let app_handle_clone = app_handle.clone();

    // Spawn background task
    tokio::spawn(async move {
        // Emit started event
        emit_plugin_event(
            &app_handle_clone,
            PluginEventType::PluginUpdateStarted,
            &plugin_name_clone,
            json!({}),
        );

        // Execute update
        let result = bridge
            .update_plugin_with_progress(
                &plugin_name_clone,
                |status, progress, message| {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUpdateProgress,
                        &plugin_name_clone,
                        json!({
                            "status": status,
                            "progress": progress,
                            "message": message
                        }),
                    );
                },
            )
            .await;

        // Emit completion event
        match result {
            Ok(result) => {
                if result.success {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUpdateCompleted,
                        &plugin_name_clone,
                        json!({
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        }),
                    );
                } else {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUpdateFailed,
                        &plugin_name_clone,
                        json!({
                            "error": result.stderr,
                        }),
                    );
                }
            }
            Err(err) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::PluginUpdateFailed,
                    &plugin_name_clone,
                    json!({
                        "error": err,
                    }),
                );
            }
        }
    });

    // Return immediately
    Ok(())
}

#[tauri::command]
pub fn uninstall_plugin(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let bridge = PythonBridge::new();
    let plugin_name_clone = plugin_name.clone();
    let app_handle_clone = app_handle.clone();

    // Spawn background task
    tokio::spawn(async move {
        // Emit started event
        emit_plugin_event(
            &app_handle_clone,
            PluginEventType::PluginUninstallStarted,
            &plugin_name_clone,
            json!({}),
        );

        // Execute uninstallation
        let result = bridge
            .uninstall_plugin_with_progress(
                &plugin_name_clone,
                |status, progress, message| {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUninstallProgress,
                        &plugin_name_clone,
                        json!({
                            "status": status,
                            "progress": progress,
                            "message": message
                        }),
                    );
                },
            )
            .await;

        // Emit completion event
        match result {
            Ok(result) => {
                if result.success {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUninstallCompleted,
                        &plugin_name_clone,
                        json!({
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        }),
                    );
                } else {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::PluginUninstallFailed,
                        &plugin_name_clone,
                        json!({
                            "error": result.stderr,
                        }),
                    );
                }
            }
            Err(err) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::PluginUninstallFailed,
                    &plugin_name_clone,
                    json!({
                        "error": err,
                    }),
                );
            }
        }
    });

    // Return immediately
    Ok(())
}

#[tauri::command]
pub fn clean_cache(
    app_handle: AppHandle,
) -> Result<(), String> {
    let bridge = PythonBridge::new();
    let app_handle_clone = app_handle.clone();

    // Spawn background task
    tokio::spawn(async move {
        // Emit started event
        emit_plugin_event(
            &app_handle_clone,
            PluginEventType::CacheCleanStarted,
            "cache",
            json!({}),
        );

        // Execute cache cleaning
        let result = bridge.clean_cache().await;

        // Emit completion event
        match result {
            Ok(result) => {
                if result.success {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::CacheCleanCompleted,
                        "cache",
                        json!({
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                        }),
                    );
                } else {
                    emit_plugin_event(
                        &app_handle_clone,
                        PluginEventType::CacheCleanFailed,
                        "cache",
                        json!({
                            "error": result.stderr,
                        }),
                    );
                }
            }
            Err(err) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::CacheCleanFailed,
                    "cache",
                    json!({
                        "error": err,
                    }),
                );
            }
        }
    });

    // Return immediately
    Ok(())
}

#[tauri::command]
pub fn get_plugin_info(
    plugin_name: String,
    app_handle: AppHandle,
) -> Result<(), String> {
    let bridge = PythonBridge::new();
    let plugin_name_clone = plugin_name.clone();
    let app_handle_clone = app_handle.clone();

    // Spawn background task
    tokio::spawn(async move {
        // Execute info retrieval
        let result = bridge.get_plugin_info(&plugin_name_clone).await;

        // Emit completion event
        match result {
            Ok(result) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::PluginInfoCompleted,
                    &plugin_name_clone,
                    json!({
                        "result": result,
                    }),
                );
            }
            Err(err) => {
                emit_plugin_event(
                    &app_handle_clone,
                    PluginEventType::PluginInfoFailed,
                    &plugin_name_clone,
                    json!({
                        "error": err,
                    }),
                );
            }
        }
    });

    // Return immediately
    Ok(())
}
