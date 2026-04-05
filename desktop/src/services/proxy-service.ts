import { invoke } from "@tauri-apps/api/core";

export interface ProxyConfig {
  enabled: boolean;
  http: string;
  https: string;
  noProxy: string;
}

export class ProxyService {
  static async save(config: ProxyConfig): Promise<void> {
    return await invoke("save_proxy_config", { config });
  }

  static async load(): Promise<ProxyConfig> {
    return await invoke<ProxyConfig>("load_proxy_config");
  }
}
