use crate::services::{MarketplaceService, PluginInfo};
use serde::{Deserialize, Serialize};
use std::process::Command as StdCommand;

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
    let output = StdCommand::new("claude")
        .args(&["plugin", "marketplace", "list", "--json"])
        .output()
        .map_err(|e| format!("Failed to execute claude plugin marketplace list: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(stderr);
    }

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let value: serde_json::Value = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse marketplace list json: {}", e))?;

    let arr = value.as_array().ok_or_else(|| "Invalid marketplace list json".to_string())?;
    let mut result = Vec::with_capacity(arr.len());
    for item in arr {
        let parsed: MarketplaceInfo = serde_json::from_value(item.clone())
            .map_err(|e| format!("Failed to parse marketplace item: {}", e))?;
        result.push(parsed);
    }

    Ok(result)
}
