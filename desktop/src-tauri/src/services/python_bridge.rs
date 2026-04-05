use crate::models::{CommandResult, InstallStatus};
use crate::utils::proxy::apply_proxy_to_command;
use std::process::Command as StdCommand;

const UVX_REPO: &str = "git+https://github.com/lazygophers/ccplugin.git@master";
const PACKAGE_NAME: &str = "lazygophers/ccplugin";

pub struct PythonBridge;

impl PythonBridge {
    pub fn new() -> Self {
        Self
    }

    /// 执行命令（无进度事件）
    async fn execute_simple(
        &self,
        program: &str,
        args: &[&str],
    ) -> Result<CommandResult, String> {
        // Spawn command in tokio runtime
        let output = tokio::task::spawn_blocking({
            let program = program.to_string();
            let program_for_error = program.clone();
            let args: Vec<String> = args.iter().map(|s| s.to_string()).collect();
            move || {
                let mut cmd = StdCommand::new(&program);
                cmd.args(&args);
                // 应用代理配置
                apply_proxy_to_command(&mut cmd);
                cmd.output()
                    .map_err(|e| format!("Failed to execute {}: {}", program_for_error, e))
            }
        })
        .await
        .map_err(|e| format!("Failed to spawn command: {}", e))??;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        Ok(CommandResult {
            success: output.status.success(),
            stdout,
            stderr,
        })
    }

    /// 安装插件（带进度回调）
    pub async fn install_plugin_with_progress<F>(
        &self,
        plugin_name: &str,
        marketplace: &str,
        scope: &str,
        mut progress_callback: F,
    ) -> Result<CommandResult, String>
    where
        F: FnMut(InstallStatus, u8, &str),
    {
        let plugin_spec = format!("{}@{}", plugin_name, marketplace);
        let args = ["plugin", "install", "--scope", scope, &plugin_spec];

        progress_callback(InstallStatus::Downloading, 10, "开始下载插件...");

        // Spawn command in tokio runtime
        let output = tokio::task::spawn_blocking({
            let program = String::from("claude");
            let args: Vec<String> = args.iter().map(|s| s.to_string()).collect();
            move || {
                let mut cmd = StdCommand::new(&program);
                cmd.args(&args);
                // 应用代理配置
                apply_proxy_to_command(&mut cmd);
                cmd.output()
                    .map_err(|e| format!("Failed to execute claude: {}", e))
            }
        })
        .await
        .map_err(|e| format!("Failed to spawn command: {}", e))??;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            progress_callback(InstallStatus::Completed, 100, "安装完成");
        } else {
            progress_callback(InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 更新插件（带进度回调）
    pub async fn update_plugin_with_progress<F>(
        &self,
        plugin_name: &str,
        mut progress_callback: F,
    ) -> Result<CommandResult, String>
    where
        F: FnMut(InstallStatus, u8, &str),
    {
        let args = ["--from", UVX_REPO, "update", PACKAGE_NAME, plugin_name];

        progress_callback(InstallStatus::Downloading, 10, "开始更新...");

        let output = tokio::task::spawn_blocking({
            let args: Vec<String> = args.iter().map(|s| s.to_string()).collect();
            move || {
                let mut cmd = StdCommand::new("uvx");
                cmd.args(&args);
                // 应用代理配置
                apply_proxy_to_command(&mut cmd);
                cmd.output()
                    .map_err(|e| format!("Failed to execute uvx: {}", e))
            }
        })
        .await
        .map_err(|e| format!("Failed to spawn command: {}", e))??;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            progress_callback(InstallStatus::Completed, 100, "更新完成");
        } else {
            progress_callback(InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 卸载插件（带进度回调）
    pub async fn uninstall_plugin_with_progress<F>(
        &self,
        plugin_name: &str,
        mut progress_callback: F,
    ) -> Result<CommandResult, String>
    where
        F: FnMut(InstallStatus, u8, &str),
    {
        let args = ["plugin", "uninstall", plugin_name];

        progress_callback(InstallStatus::Installing, 10, "开始卸载插件...");

        let output = tokio::task::spawn_blocking({
            let args: Vec<String> = args.iter().map(|s| s.to_string()).collect();
            move || {
                let mut cmd = StdCommand::new("claude");
                cmd.args(&args);
                // 应用代理配置
                apply_proxy_to_command(&mut cmd);
                cmd.output()
                    .map_err(|e| format!("Failed to execute claude: {}", e))
            }
        })
        .await
        .map_err(|e| format!("Failed to spawn command: {}", e))??;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            progress_callback(InstallStatus::Completed, 100, "卸载完成");
        } else {
            progress_callback(InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 清理缓存
    pub async fn clean_cache(&self) -> Result<CommandResult, String> {
        self.execute_simple("uvx", &["--from", UVX_REPO, "clean", PACKAGE_NAME])
            .await
    }

    /// 获取插件信息
    pub async fn get_plugin_info(&self, plugin_name: &str) -> Result<CommandResult, String> {
        self.execute_simple("uvx", &["--from", UVX_REPO, "info", PACKAGE_NAME, plugin_name])
            .await
    }
}
