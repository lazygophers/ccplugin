use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
struct MarketplaceJson {
    #[allow(dead_code)]
    name: String,
    plugins: Vec<MarketplacePlugin>,
}

#[derive(Debug, Deserialize)]
struct MarketplacePlugin {
    name: String,
    #[serde(default)]
    source: String,
    description: String,
    version: String,
    #[serde(default)]
    author: PluginAuthor,
    #[serde(default)]
    keywords: Vec<String>,
}

#[derive(Debug, Default, Deserialize)]
struct PluginAuthor {
    name: String,
    #[serde(default)]
    #[allow(dead_code)]
    email: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct PluginInfo {
    pub name: String,
    pub version: String,
    pub description: String,
    pub author: String,
    pub keywords: Vec<String>,
    pub category: String,
    pub installed: bool,
    pub installed_version: Option<String>,
}

pub struct MarketplaceService;

impl MarketplaceService {
    /// 获取marketplace.json路径
    fn get_marketplace_path() -> PathBuf {
        // 相对于项目根目录
        let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        path.pop(); // 移除 src-tauri
        path.pop(); // 移除 desktop
        path.push(".claude-plugin");
        path.push("marketplace.json");
        path
    }

    /// 获取Claude插件缓存目录
    fn get_claude_plugins_dir() -> Option<PathBuf> {
        let home = dirs::home_dir()?;
        Some(home.join(".claude/plugins/cache/ccplugin-market"))
    }

    /// 读取marketplace.json
    pub fn load_marketplace() -> Result<Vec<PluginInfo>, String> {
        let path = Self::get_marketplace_path();

        if !path.exists() {
            return Err(format!("Marketplace file not found: {}", path.display()));
        }

        let content = fs::read_to_string(&path)
            .map_err(|e| format!("Failed to read marketplace.json: {}", e))?;

        let marketplace: MarketplaceJson = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse marketplace.json: {}", e))?;

        let installed_plugins = Self::get_installed_plugins();

        let plugins = marketplace
            .plugins
            .into_iter()
            .map(|p| {
                let category = Self::infer_category(&p.source);
                let installed = installed_plugins.contains(&p.name);
                let installed_version = if installed {
                    Some(p.version.clone())
                } else {
                    None
                };

                PluginInfo {
                    name: p.name,
                    version: p.version,
                    description: p.description,
                    author: p.author.name,
                    keywords: p.keywords,
                    category,
                    installed,
                    installed_version,
                }
            })
            .collect();

        Ok(plugins)
    }

    /// 获取已安装的插件列表
    pub fn get_installed_plugins() -> Vec<String> {
        let mut installed = Vec::new();

        if let Some(plugins_dir) = Self::get_claude_plugins_dir() {
            if plugins_dir.exists() {
                if let Ok(entries) = fs::read_dir(plugins_dir) {
                    for entry in entries.flatten() {
                        if entry.path().is_dir() {
                            if let Some(name) = entry.file_name().to_str() {
                                installed.push(name.to_string());
                            }
                        }
                    }
                }
            }
        }

        installed
    }

    /// 从source路径推断插件分类
    fn infer_category(source: &str) -> String {
        if source.contains("/languages/") {
            "languages".to_string()
        } else if source.contains("/tools/") {
            "tools".to_string()
        } else if source.contains("/office/") {
            "office".to_string()
        } else if source.contains("/novels/") {
            "novels".to_string()
        } else {
            "other".to_string()
        }
    }

    /// 搜索插件
    pub fn search_plugins(query: &str, plugins: &[PluginInfo]) -> Vec<PluginInfo> {
        let query_lower = query.to_lowercase();

        plugins
            .iter()
            .filter(|p| {
                p.name.to_lowercase().contains(&query_lower)
                    || p.description.to_lowercase().contains(&query_lower)
                    || p.keywords.iter().any(|k| k.to_lowercase().contains(&query_lower))
            })
            .cloned()
            .collect()
    }

    /// 按分类过滤插件
    pub fn filter_by_category(category: &str, plugins: &[PluginInfo]) -> Vec<PluginInfo> {
        if category == "all" {
            plugins.to_vec()
        } else {
            plugins
                .iter()
                .filter(|p| p.category == category)
                .cloned()
                .collect()
        }
    }
}
