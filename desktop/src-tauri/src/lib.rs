mod commands;
mod events;
mod models;
mod services;
mod utils;

use tauri::{menu::{MenuBuilder, MenuItemBuilder}, tray::{TrayIconBuilder, MouseButton, MouseButtonState}, Manager};

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
        // Setup
        .setup(|app| {
            // 初始化通知服务
            crate::services::init_notification_service(&app.handle())?;

            // 初始化任务队列（最多同时执行2个任务）
            crate::services::init_task_queue(2)?;
            if let Some(task_queue) = crate::services::task_queue() {
                task_queue.start_processor(app.handle());
            }

            // 读取并设置代理配置
            if let Ok(store) = app.path().app_local_data_dir() {
                let config_path = store.join("ccplugin-proxy.json");
                if let Ok(content) = std::fs::read_to_string(&config_path) {
                    if let Ok(config) = serde_json::from_str::<serde_json::Value>(&content) {
                        if config.get("enabled").and_then(|v| v.as_bool()).unwrap_or(false) {
                            if let Some(http) = config.get("http").and_then(|v| v.as_str()) {
                                if !http.is_empty() {
                                    std::env::set_var("HTTP_PROXY", http);
                                    std::env::set_var("http_proxy", http);
                                }
                            }
                            if let Some(https) = config.get("https").and_then(|v| v.as_str()) {
                                if !https.is_empty() {
                                    std::env::set_var("HTTPS_PROXY", https);
                                    std::env::set_var("https_proxy", https);
                                }
                            }
                            if let Some(no_proxy) = config.get("noProxy").and_then(|v| v.as_str()) {
                                if !no_proxy.is_empty() {
                                    std::env::set_var("NO_PROXY", no_proxy);
                                    std::env::set_var("no_proxy", no_proxy);
                                }
                            }
                        }
                    }
                }
            }

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
            commands::uninstall_plugin,
            commands::get_tasks,
            commands::get_task_status,
            commands::get_marketplace_plugins,
            commands::get_installed_plugins,
            commands::get_marketplaces,
            commands::update_marketplace,
            commands::search_plugins,
            commands::filter_plugins_by_category,
            commands::proxy::save_proxy_config,
            commands::proxy::load_proxy_config,
            commands::add_notification,
            commands::get_notifications,
            commands::get_unread_count,
            commands::mark_notification_read,
            commands::mark_all_notifications_read,
            commands::update_notification,
            commands::delete_notification,
            commands::clear_all_notifications,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
