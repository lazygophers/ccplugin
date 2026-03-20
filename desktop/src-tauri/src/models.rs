use serde::{Deserialize, Serialize};

/// Python命令执行结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

/// 插件安装进度事件
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PluginInstallProgress {
    pub plugin_name: String,
    pub status: InstallStatus,
    pub progress: u8, // 0-100
    pub message: String,
}

/// 插件安装状态
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum InstallStatus {
    Downloading,
    Installing,
    Completed,
    Failed,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_result_serialization() {
        let result = CommandResult {
            success: true,
            stdout: "test output".to_string(),
            stderr: "".to_string(),
        };

        let json = serde_json::to_string(&result).unwrap();
        assert!(json.contains("\"success\":true"));
        assert!(json.contains("test output"));
    }

    #[test]
    fn test_install_status_serialization() {
        let status = InstallStatus::Downloading;
        let json = serde_json::to_string(&status).unwrap();
        assert_eq!(json, "\"downloading\"");
    }
}
