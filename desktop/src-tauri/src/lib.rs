mod commands;
mod services;

use commands::PythonBridgeState;
use std::sync::Arc;
use tauri::{menu::{MenuBuilder, MenuItemBuilder}, tray::{TrayIconBuilder, MouseButton, MouseButtonState}, Manager};
use tokio::sync::Mutex;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        // Plugins
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            Some(vec!["--minimized"]),
        ))
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let _ = app
                .get_webview_window("main")
                .expect("no main window")
                .set_focus();
        }))
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        // State
        .manage(PythonBridgeState(Arc::new(Mutex::new(None))))
        // Setup
        .setup(|app| {
            // System tray menu
            let show_i = MenuItemBuilder::with_id("show", "显示窗口").build(app)?;
            let hide_i = MenuItemBuilder::with_id("hide", "隐藏窗口").build(app)?;
            let quit_i = MenuItemBuilder::with_id("quit", "退出").build(app)?;

            let menu = MenuBuilder::new(app)
                .items(&[&show_i, &hide_i, &quit_i])
                .build()?;

            // System tray
            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .icon(app.default_window_icon().unwrap().clone())
                .on_menu_event(|app, event| match event.id().as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let tauri::tray::TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        // Window events
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // 关闭窗口时隐藏到托盘而非退出
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        // Commands
        .invoke_handler(tauri::generate_handler![
            commands::install_plugin,
            commands::update_plugin,
            commands::clean_cache,
            commands::get_plugin_info,
            commands::get_marketplace_plugins,
            commands::get_installed_plugins,
            commands::search_plugins,
            commands::filter_plugins_by_category,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
