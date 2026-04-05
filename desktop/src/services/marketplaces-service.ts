import { invoke } from "@tauri-apps/api/core";

export interface MarketplaceInfo {
  name: string;
  source?: string;
  url?: string;
  installLocation?: string;
}

export class MarketplacesService {
  static async list(): Promise<MarketplaceInfo[]> {
    return await invoke<MarketplaceInfo[]>("get_marketplaces");
  }

  static async update(marketplaceName: string): Promise<string> {
    return await invoke<string>("update_marketplace", { marketplaceName });
  }
}

