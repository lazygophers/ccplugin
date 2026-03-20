use crate::services::{MarketplaceService, PluginInfo};

#[tauri::command]
pub fn get_marketplace_plugins() -> Result<Vec<PluginInfo>, String> {
    MarketplaceService::load_marketplace()
}

#[tauri::command]
pub fn get_installed_plugins() -> Vec<String> {
    MarketplaceService::get_installed_plugins()
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
