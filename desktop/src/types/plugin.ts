export interface Plugin {
  name: string;
  version: string;
  marketplace: string;
  description: string;
  author: string;
  keywords: string[];
  category: PluginCategory;
}

export type PluginCategory = "tools" | "languages" | "office" | "other";

export interface PluginInstallProgress {
  plugin_name: string;
  status: InstallStatus;
  progress: number; // 0-100
  message: string;
}

export type InstallStatus = "downloading" | "installing" | "completed" | "failed";

export interface CommandResult {
  success: boolean;
  stdout: string;
  stderr: string;
}
