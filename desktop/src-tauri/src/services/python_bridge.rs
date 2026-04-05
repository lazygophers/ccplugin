use crate::models::{CommandResult, PluginInstallProgress, InstallStatus};
use tauri::{AppHandle, Emitter};
use std::process::Command as StdCommand;

const UVX_REPO: &str = "git+https://github.com/lazygophers/ccplugin.git@master";
const PACKAGE_NAME: &str = "lazygophers/ccplugin";

pub struct PythonBridge {
    app_handle: AppHandle,
}

impl PythonBridge {
    pub fn new(app_handle: AppHandle) -> Self {
        Self { app_handle }
    }

    /// 执行命令并发送进度事件
    async fn execute_with_progress(
        &self,
        plugin_name: &str,
        program: &str,
        args: &[&str],
        initial_status: InstallStatus,
        initial_progress: u8,
        initial_message: &str,
        success_message: &str,
    ) -> Result<CommandResult, String> {
        self.emit_progress(plugin_name, initial_status, initial_progress, initial_message);

        let output = StdCommand::new(program)
            .args(args)
            .output()
            .map_err(|e| format!("Failed to execute {}: {}", program, e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            self.emit_progress(plugin_name, InstallStatus::Completed, 100, success_message);
        } else {
            self.emit_progress(plugin_name, InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 执行命令（无进度事件）
    async fn execute_simple(
        &self,
        program: &str,
        args: &[&str],
    ) -> Result<CommandResult, String> {
        let output = StdCommand::new(program)
            .args(args)
            .output()
            .map_err(|e| format!("Failed to execute {}: {}", program, e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        Ok(CommandResult {
            success: output.status.success(),
            stdout,
            stderr,
        })
    }

    /// 安装插件
    pub async fn install_plugin(
        &self,
        plugin_name: &str,
        marketplace: &str,
        scope: &str,
    ) -> Result<CommandResult, String> {
        let plugin_spec = format!("{}@{}", plugin_name, marketplace);
        self.execute_with_progress(
            plugin_name,
            "claude",
            &["plugin", "install", "--scope", scope, &plugin_spec],
            InstallStatus::Downloading,
            10,
            "开始下载插件...",
            "安装完成",
        )
        .await
    }

    /// 更新插件
    pub async fn update_plugin(&self, plugin_name: &str) -> Result<CommandResult, String> {
        self.execute_with_progress(
            plugin_name,
            "uvx",
            &["--from", UVX_REPO, "update", PACKAGE_NAME, plugin_name],
            InstallStatus::Downloading,
            10,
            "开始更新插件...",
            "更新完成",
        )
        .await
    }

    /// 卸载插件
    pub async fn uninstall_plugin(&self, plugin_name: &str) -> Result<CommandResult, String> {
        self.execute_with_progress(
            plugin_name,
            "claude",
            &["plugin", "uninstall", plugin_name],
            InstallStatus::Installing,
            10,
            "开始卸载插件...",
            "卸载完成",
        )
        .await
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

    /// 发送进度事件到前端
    fn emit_progress(&self, plugin_name: &str, status: InstallStatus, progress: u8, message: &str) {
        let progress_data = PluginInstallProgress {
            plugin_name: plugin_name.to_string(),
            status,
            progress,
            message: message.to_string(),
        };

        let _ = self.app_handle.emit("plugin-install-progress", progress_data);
    }
}
