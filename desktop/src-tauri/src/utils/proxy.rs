use serde::Deserialize;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Deserialize)]
struct ProxyConfig {
    pub enabled: bool,
    #[serde(default)]
    pub http: String,
    #[serde(default)]
    pub https: String,
    #[serde(default)]
    pub no_proxy: String,
}

fn get_proxy_config_path() -> Option<PathBuf> {
    // 尝试从多个可能的配置路径读取
    let paths = vec![
        dirs::home_dir()?.join(".config/com.lazygophers.ccplugin-desktop/ccplugin-proxy.json"),
        dirs::home_dir()?.join(".claude/ccplugin-desktop/ccplugin-proxy.json"),
    ];

    for path in paths {
        if path.exists() {
            return Some(path);
        }
    }
    None
}

pub fn load_proxy_config() -> Option<ProxyConfig> {
    let config_path = get_proxy_config_path()?;
    let content = fs::read_to_string(&config_path).ok()?;
    serde_json::from_str(&content).ok()
}

/// 为 Command 设置代理环境变量
/// 返回是否成功设置了代理
pub fn apply_proxy_to_command(cmd: &mut std::process::Command) -> bool {
    if let Some(config) = load_proxy_config() {
        if config.enabled {
            if !config.http.is_empty() {
                cmd.env("HTTP_PROXY", &config.http);
                cmd.env("http_proxy", &config.http);
            }
            if !config.https.is_empty() {
                cmd.env("HTTPS_PROXY", &config.https);
                cmd.env("https_proxy", &config.https);
            }
            if !config.no_proxy.is_empty() {
                cmd.env("NO_PROXY", &config.no_proxy);
                cmd.env("no_proxy", &config.no_proxy);
            }
            return true;
        }
    }
    false
}

/// 获取代理配置信息（用于调试）
pub fn get_proxy_info() -> String {
    if let Some(config) = load_proxy_config() {
        if config.enabled {
            let mut info = vec!["代理已启用".to_string()];
            if !config.http.is_empty() {
                info.push(format!("HTTP: {}", config.http));
            }
            if !config.https.is_empty() {
                info.push(format!("HTTPS: {}", config.https));
            }
            if !config.no_proxy.is_empty() {
                info.push(format!("NO_PROXY: {}", config.no_proxy));
            }
            info.join("\n")
        } else {
            "代理已禁用".to_string()
        }
    } else {
        "未配置代理".to_string()
    }
}
