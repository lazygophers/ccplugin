use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::process::Command;

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
    homepage: String,
    #[serde(default)]
    repository: String,
    #[serde(default)]
    license: String,
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

/// Claude plugin list --json 输出格式
#[derive(Debug, Deserialize)]
struct ClaudePluginListOutput {
    id: String,
    version: String,
    scope: String,
}

/// 已安装插件信息（从 claude plugin list 获取）
#[derive(Debug, Clone)]
struct InstalledPluginInfo {
    name: String,
    version: String,
    scope: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct PluginInfo {
    pub name: String,
    pub version: String,
    pub description: String,
    pub author: String,
    pub homepage: String,
    pub repository: String,
    pub license: String,
    pub source: String,
    pub keywords: Vec<String>,
    pub category: String,
    pub installed: bool,
    pub installed_version: Option<String>,
    pub installed_scope: Option<String>,
    pub marketplace: String,
}

pub struct MarketplaceService;

impl MarketplaceService {
    const EMBEDDED_MARKETPLACE_JSON: &'static str =
        include_str!("../../../../.claude-plugin/marketplace.json");

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

    fn read_marketplace_json() -> Result<String, String> {
        let path = Self::get_marketplace_path();

        // 直接读取文件，不存在时使用内置 JSON
        match fs::read_to_string(&path) {
            Ok(content) => Ok(content),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                Ok(Self::EMBEDDED_MARKETPLACE_JSON.to_string())
            }
            Err(e) => Err(format!("Failed to read marketplace.json: {}", e)),
        }
    }

    /// 读取marketplace.json（包含外部 marketplace 扫描）
    pub fn load_marketplace() -> Result<Vec<PluginInfo>, String> {
        let mut all_plugins = Vec::new();

        // 获取已安装插件列表（从 claude plugin list）
        let installed_plugins = Self::get_installed_plugins();

        // 1. 从项目 marketplace.json 读取
        let content = Self::read_marketplace_json()?;

        let marketplace: MarketplaceJson = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse marketplace.json: {}", e))?;

        let json_plugins = marketplace
            .plugins
            .into_iter()
            .map(|p| {
                let category = Self::infer_category(&p.source);
                let installed_info = installed_plugins.iter().find(|info| info.name == p.name);
                let installed = installed_info.is_some();
                let (installed_version, installed_scope) = if let Some(info) = installed_info {
                    (Some(info.version.clone()), Some(info.scope.clone()))
                } else {
                    (None, None)
                };

                PluginInfo {
                    name: p.name,
                    version: p.version,
                    description: p.description,
                    author: p.author.name,
                    homepage: p.homepage,
                    repository: p.repository,
                    license: p.license,
                    source: p.source,
                    keywords: p.keywords,
                    category,
                    installed,
                    installed_version,
                    installed_scope,
                    marketplace: "ccplugin-market".to_string(),
                }
            })
            .collect::<Vec<_>>();

        all_plugins.extend(json_plugins);

        // 2. 扫描外部 marketplace（如 claude-plugins-official）
        let home = match dirs::home_dir() {
            Some(h) => h,
            None => return Ok(all_plugins),
        };

        let marketplaces_dir = home.join(".claude/plugins/marketplaces");
        if marketplaces_dir.exists() {
            if let Ok(entries) = fs::read_dir(marketplaces_dir) {
                for entry in entries.flatten() {
                    let marketplace_name = entry.file_name();
                    if let Some(name_str) = marketplace_name.to_str() {
                        // 跳过已通过 marketplace.json 定义的 marketplace
                        if name_str == "ccplugin-market" {
                            continue;
                        }

                        let external_plugins = Self::scan_external_marketplace(name_str, &installed_plugins);
                        all_plugins.extend(external_plugins);
                    }
                }
            }
        }

        Ok(all_plugins)
    }

    /// 获取已安装的插件列表（使用 claude plugin list --json）
    fn get_installed_plugins() -> Vec<InstalledPluginInfo> {
        let output = Command::new("claude")
            .args(&["plugin", "list", "--json"])
            .output()
            .map_err(|e| format!("Failed to run claude plugin list: {}", e));

        let mut installed = Vec::new();

        if let Ok(output) = output {
            if output.status.success() {
                if let Ok(plugins) = serde_json::from_slice::<Vec<ClaudePluginListOutput>>(&output.stdout) {
                    for plugin in plugins {
                        // id 格式可能是 "plugin@market" 或 "plugin"
                        let name = plugin.id.split('@').next().unwrap_or(&plugin.id);
                        installed.push(InstalledPluginInfo {
                            name: name.to_string(),
                            version: plugin.version,
                            scope: plugin.scope,
                        });
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

    /// 从文件系统扫描外部 marketplace 的插件
    fn scan_external_marketplace(marketplace_name: &str, installed_plugins: &[InstalledPluginInfo]) -> Vec<PluginInfo> {
        let mut plugins = Vec::new();

        let home = match dirs::home_dir() {
            Some(h) => h,
            None => return plugins,
        };

        let marketplace_path = home.join(".claude/plugins/marketplaces").join(marketplace_name);
        let plugins_path = marketplace_path.join("plugins");

        if !plugins_path.exists() {
            return plugins;
        }

        if let Ok(entries) = fs::read_dir(&plugins_path) {
            for entry in entries.flatten() {
                let plugin_path = entry.path();
                if !plugin_path.is_dir() {
                    continue;
                }

                let plugin_json_path = plugin_path.join(".claude-plugin").join("plugin.json");
                if !plugin_json_path.exists() {
                    continue;
                }

                // 读取插件的 plugin.json
                if let Ok(content) = fs::read_to_string(&plugin_json_path) {
                    if let Ok(plugin_json) = serde_json::from_str::<serde_json::Value>(&content) {
                        let name_from_json: Option<&str> = plugin_json.get("name")
                            .and_then(|v| v.as_str());

                        let fallback_name = plugin_path.file_name()
                            .expect("plugin path should have a file name")
                            .to_string_lossy()
                            .into_owned();

                        let name: String = match name_from_json {
                            Some(s) => s.to_string(),
                            None => fallback_name,
                        };

                        let description = plugin_json.get("description")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string();

                        let version = plugin_json.get("version")
                            .and_then(|v| v.as_str())
                            .unwrap_or("unknown")
                            .to_string();

                        let author_name = plugin_json.get("author")
                            .and_then(|v| v.as_object())
                            .and_then(|obj| obj.get("name"))
                            .and_then(|v| v.as_str())
                            .unwrap_or("Unknown")
                            .to_string();

                        let keywords = plugin_json.get("keywords")
                            .and_then(|v| v.as_array())
                            .map(|arr| {
                                arr.iter()
                                    .filter_map(|v| v.as_str())
                                    .map(String::from)
                                    .collect::<Vec<_>>()
                            })
                            .unwrap_or_default();

                        // 推断 source 和 category
                        let source = format!("./{}/{}", marketplace_name, name);
                        let category = Self::infer_category(&source);

                        let installed_info = installed_plugins.iter().find(|info| info.name == name);
                        let installed = installed_info.is_some();
                        let (installed_version, installed_scope) = if let Some(info) = installed_info {
                            (Some(info.version.clone()), Some(info.scope.clone()))
                        } else {
                            (None, None)
                        };

                        plugins.push(PluginInfo {
                            name,
                            version,
                            description,
                            author: author_name,
                            homepage: String::new(),
                            repository: String::new(),
                            license: String::new(),
                            source,
                            keywords,
                            category,
                            installed,
                            installed_version,
                            installed_scope,
                            marketplace: marketplace_name.to_string(),
                        });
                    }
                }
            }
        }

        plugins
    }

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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn infer_category_handles_known_paths() {
        assert_eq!(
            MarketplaceService::infer_category("./plugins/tools/git"),
            "tools"
        );
        assert_eq!(
            MarketplaceService::infer_category("./plugins/languages/python"),
            "languages"
        );
        assert_eq!(
            MarketplaceService::infer_category("./plugins/office/docx"),
            "office"
        );
        assert_eq!(
            MarketplaceService::infer_category("./plugins/novels/novel"),
            "novels"
        );
        assert_eq!(MarketplaceService::infer_category("./plugins/other/x"), "other");
    }

    #[test]
    fn search_plugins_matches_name_description_and_keywords() {
        let plugins = vec![
            PluginInfo {
                name: "git".to_string(),
                version: "1.0.0".to_string(),
                description: "Git 操作".to_string(),
                author: "a".to_string(),
                homepage: "".to_string(),
                repository: "".to_string(),
                license: "".to_string(),
                source: "".to_string(),
                keywords: vec!["commit".to_string()],
                category: "tools".to_string(),
                installed: false,
                installed_version: None,
                marketplace: "test-market".to_string(),
            },
            PluginInfo {
                name: "python".to_string(),
                version: "1.0.0".to_string(),
                description: "语言规范".to_string(),
                author: "b".to_string(),
                homepage: "".to_string(),
                repository: "".to_string(),
                license: "".to_string(),
                source: "".to_string(),
                keywords: vec!["typing".to_string()],
                category: "languages".to_string(),
                installed: false,
                installed_version: None,
                marketplace: "test-market".to_string(),
            },
        ];

        assert_eq!(MarketplaceService::search_plugins("git", &plugins).len(), 1);
        assert_eq!(MarketplaceService::search_plugins("语言", &plugins).len(), 1);
        assert_eq!(MarketplaceService::search_plugins("commit", &plugins).len(), 1);
        assert_eq!(MarketplaceService::search_plugins("missing", &plugins).len(), 0);
    }

    #[test]
    fn filter_by_category_all_returns_all() {
        let plugins = vec![
            PluginInfo {
                name: "a".to_string(),
                version: "1".to_string(),
                description: "d".to_string(),
                author: "x".to_string(),
                homepage: "".to_string(),
                repository: "".to_string(),
                license: "".to_string(),
                source: "".to_string(),
                keywords: vec![],
                category: "tools".to_string(),
                installed: false,
                installed_version: None,
                marketplace: "test-market".to_string(),
            },
            PluginInfo {
                name: "b".to_string(),
                version: "1".to_string(),
                description: "d".to_string(),
                author: "x".to_string(),
                homepage: "".to_string(),
                repository: "".to_string(),
                license: "".to_string(),
                source: "".to_string(),
                keywords: vec![],
                category: "languages".to_string(),
                installed: false,
                installed_version: None,
                marketplace: "test-market".to_string(),
            },
        ];

        assert_eq!(MarketplaceService::filter_by_category("all", &plugins).len(), 2);
        assert_eq!(MarketplaceService::filter_by_category("tools", &plugins).len(), 1);
    }
}
