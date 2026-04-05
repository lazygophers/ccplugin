use serde::{Deserialize, Serialize};
use std::fs;
use std::io::Write;
use tauri::Manager;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProxyConfig {
    pub enabled: bool,
    #[serde(default)]
    pub http: String,
    #[serde(default)]
    pub https: String,
    #[serde(default = "default_no_proxy")]
    pub no_proxy: String,
}

fn default_no_proxy() -> String {
    "localhost,127.0.0.1".to_string()
}

#[tauri::command]
pub fn save_proxy_config(config: ProxyConfig, app_handle: tauri::AppHandle) -> Result<(), String> {
    let app_local_data_dir = app_handle
        .path()
        .app_local_data_dir()
        .map_err(|e| format!("Failed to get app local data dir: {}", e))?;

    // 确保目录存在
    fs::create_dir_all(&app_local_data_dir)
        .map_err(|e| format!("Failed to create directory: {}", e))?;

    let config_path = app_local_data_dir.join("ccplugin-proxy.json");
    let json = serde_json::to_string_pretty(&config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    let mut file = fs::File::create(&config_path)
        .map_err(|e| format!("Failed to create config file: {}", e))?;

    file.write_all(json.as_bytes())
        .map_err(|e| format!("Failed to write config: {}", e))?;

    Ok(())
}

#[tauri::command]
pub fn load_proxy_config(app_handle: tauri::AppHandle) -> Result<ProxyConfig, String> {
    let app_local_data_dir = app_handle
        .path()
        .app_local_data_dir()
        .map_err(|e| format!("Failed to get app local data dir: {}", e))?;

    let config_path = app_local_data_dir.join("ccplugin-proxy.json");

    if !config_path.exists() {
        return Ok(ProxyConfig {
            enabled: false,
            http: String::new(),
            https: String::new(),
            no_proxy: default_no_proxy(),
        });
    }

    let content = fs::read_to_string(&config_path)
        .map_err(|e| format!("Failed to read config file: {}", e))?;

    let config: ProxyConfig = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse config: {}", e))?;

    Ok(config)
}
