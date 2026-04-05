use crate::services::{MarketplaceService, PluginInfo};
use crate::utils;
use serde::{Deserialize, Serialize};
use std::process::Command;

#[tauri::command]
pub fn get_marketplace_plugins() -> Result<Vec<PluginInfo>, String> {
    MarketplaceService::load_marketplace()
}

#[tauri::command]
pub fn get_installed_plugins() -> Vec<String> {
    // 从 PluginInfo 中提取已安装插件的名称
    if let Ok(plugins) = MarketplaceService::load_marketplace() {
        plugins
            .into_iter()
            .filter(|p| p.installed)
            .map(|p| p.name)
            .collect()
    } else {
        Vec::new()
    }
}

#[tauri::command]
pub fn search_plugins(query: String) -> Result<Vec<PluginInfo>, String> {
    let all_plugins = MarketplaceService::load_marketplace()?;
    Ok(MarketplaceService::search_plugins(&query, &all_plugins))
}

#[tauri::command]
pub fn filter_plugins_by_category(category: String) -> Result<Vec<PluginInfo>, String> {
    let all_plugins = MarketplaceService::load_marketplace()?;
    Ok(MarketplaceService::filter_by_category(&category, &all_plugins))
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketplaceInfo {
    pub name: String,
    #[serde(default)]
    pub source: String,
    #[serde(default)]
    pub url: String,
    #[serde(rename = "installLocation", default)]
    pub install_location: String,
}

#[tauri::command]
pub fn get_marketplaces() -> Result<Vec<MarketplaceInfo>, String> {
    use std::fs;

    let home = dirs::home_dir().ok_or_else(|| "Failed to get home directory".to_string())?;
    let marketplaces_dir = home.join(".claude/plugins/marketplaces");

    if !marketplaces_dir.exists() {
        return Ok(Vec::new());
    }

    let mut result = Vec::new();

    let entries = fs::read_dir(&marketplaces_dir)
        .map_err(|e| format!("Failed to read marketplaces directory: {}", e))?;

    for entry in entries.flatten() {
        let path = entry.path();

        // 跳过非目录项
        if !path.is_dir() {
            continue;
        }

        // 尝试读取 marketplace.json
        let manifest_path = path.join("marketplace.json");
        let (name, source, install_location, url) = if manifest_path.exists() {
            let content = fs::read_to_string(&manifest_path)
                .map_err(|e| format!("Failed to read marketplace.json: {}", e))?;

            let json: serde_json::Value = serde_json::from_str(&content)
                .map_err(|e| format!("Failed to parse marketplace.json: {}", e))?;

            let name = json.get("name")
                .and_then(|v| v.as_str())
                .unwrap_or_else(|| {
                    path.file_name()
                        .and_then(|n| n.to_str())
                        .unwrap_or("unknown")
                })
                .to_string();

            let source = json.get("source")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();

            let url = json.get("url")
                .and_then(|v| v.as_str())
                .unwrap_or("")
                .to_string();

            let install_location = json.get("installLocation")
                .map(|s| s.to_string())
                .unwrap_or_else(|| {
                    // 默认安装位置
                    let default_path = home.join(".claude/plugins/marketplaces").join(&name);
                    default_path.to_string_lossy().to_string()
                });

            (name, source, install_location, url)
        } else {
            // 如果没有 marketplace.json，使用目录名
            let name = path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string();

            let source = path.to_string_lossy().to_string();
            let install_location = path.to_string_lossy().to_string();
            let url = String::new();

            (name, source, install_location, url)
        };

        result.push(MarketplaceInfo {
            name,
            source,
            url,
            install_location,
        });
    }

    Ok(result)
}

#[tauri::command]
pub async fn update_marketplace(marketplace_name: String) -> Result<String, String> {
    let mut cmd = Command::new("claude");
    cmd.args(["plugin", "marketplace", "update", &marketplace_name]);

    // 应用代理配置
    utils::apply_proxy_to_command(&mut cmd);

    let output = cmd
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        Ok(stdout.trim().to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        Err(stderr.trim().to_string())
    }
}
