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

    /// 安装插件
    pub async fn install_plugin(
        &self,
        plugin_name: &str,
        marketplace: &str,
    ) -> Result<CommandResult, String> {
        let plugin_spec = format!("{}@{}", plugin_name, marketplace);

        // 发送开始安装事件
        self.emit_progress(&plugin_name, InstallStatus::Downloading, 10, "开始下载插件...");

        let output = StdCommand::new("uvx")
            .args(&[
                "--from",
                UVX_REPO,
                "install",
                PACKAGE_NAME,
                &plugin_spec,
            ])
            .output()
            .map_err(|e| format!("Failed to execute uvx: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            self.emit_progress(&plugin_name, InstallStatus::Completed, 100, "安装完成");
        } else {
            self.emit_progress(&plugin_name, InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 更新插件
    pub async fn update_plugin(&self, plugin_name: &str) -> Result<CommandResult, String> {
        self.emit_progress(&plugin_name, InstallStatus::Downloading, 10, "开始更新插件...");

        let output = StdCommand::new("uvx")
            .args(&["--from", UVX_REPO, "update", PACKAGE_NAME, plugin_name])
            .output()
            .map_err(|e| format!("Failed to execute uvx update: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let success = output.status.success();

        if success {
            self.emit_progress(&plugin_name, InstallStatus::Completed, 100, "更新完成");
        } else {
            self.emit_progress(&plugin_name, InstallStatus::Failed, 0, &stderr);
        }

        Ok(CommandResult {
            success,
            stdout,
            stderr,
        })
    }

    /// 清理缓存
    pub async fn clean_cache(&self) -> Result<CommandResult, String> {
        let output = StdCommand::new("uvx")
            .args(&["--from", UVX_REPO, "clean", PACKAGE_NAME])
            .output()
            .map_err(|e| format!("Failed to execute uvx clean: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        Ok(CommandResult {
            success: output.status.success(),
            stdout,
            stderr,
        })
    }

    /// 获取插件信息
    pub async fn get_plugin_info(&self, plugin_name: &str) -> Result<CommandResult, String> {
        let output = StdCommand::new("uvx")
            .args(&["--from", UVX_REPO, "info", PACKAGE_NAME, plugin_name])
            .output()
            .map_err(|e| format!("Failed to execute uvx info: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();

        Ok(CommandResult {
            success: output.status.success(),
            stdout,
            stderr,
        })
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
