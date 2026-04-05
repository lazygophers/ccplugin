import { describe, it, expect, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { MarketplaceService } from "./marketplace-service";

describe("MarketplaceService", () => {
  it("getAllPlugins calls get_marketplace_plugins", async () => {
    const mock = [{ name: "python" }];
    vi.mocked(invoke).mockResolvedValueOnce(mock);
    await expect(MarketplaceService.getAllPlugins()).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("get_marketplace_plugins");
  });

  it("getInstalledPlugins calls get_installed_plugins", async () => {
    const mock = ["python"];
    vi.mocked(invoke).mockResolvedValueOnce(mock);
    await expect(MarketplaceService.getInstalledPlugins()).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("get_installed_plugins");
  });

  it("searchPlugins calls search_plugins", async () => {
    const mock = [{ name: "git" }];
    vi.mocked(invoke).mockResolvedValueOnce(mock);
    await expect(MarketplaceService.searchPlugins("git")).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("search_plugins", { query: "git" });
  });

  it("filterByCategory calls filter_plugins_by_category", async () => {
    const mock = [{ name: "python" }];
    vi.mocked(invoke).mockResolvedValueOnce(mock);
    await expect(MarketplaceService.filterByCategory("languages")).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("filter_plugins_by_category", { category: "languages" });
  });
});
