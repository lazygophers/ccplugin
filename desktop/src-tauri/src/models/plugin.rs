use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Plugin {
    pub name: String,
    pub version: String,
    pub marketplace: String,
    pub description: String,
    pub author: String,
    pub keywords: Vec<String>,
    pub category: PluginCategory,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PluginCategory {
    Tools,
    Languages,
    Office,
    Other,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginInstallProgress {
    pub plugin_name: String,
    pub status: InstallStatus,
    pub progress: u8, // 0-100
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum InstallStatus {
    Downloading,
    Installing,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}
