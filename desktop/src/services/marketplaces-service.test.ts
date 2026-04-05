import { describe, it, expect, vi, beforeEach } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { MarketplacesService } from "./marketplaces-service";

describe("MarketplacesService", () => {
  beforeEach(() => {
    vi.mocked(invoke).mockReset();
  });

  it("list invokes get_marketplaces", async () => {
    const mock = [{ name: "ccplugin-market", url: "x", source: "y", installLocation: "z" }];
    vi.mocked(invoke).mockResolvedValueOnce(mock);

    await expect(MarketplacesService.list()).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("get_marketplaces");
  });

  it("update calls update_marketplace with marketplace name", async () => {
    vi.mocked(invoke).mockResolvedValueOnce("Updated successfully");

    await expect(MarketplacesService.update("ccplugin-market")).resolves.toBe("Updated successfully");
    expect(invoke).toHaveBeenCalledWith("update_marketplace", { marketplaceName: "ccplugin-market" });
  });

  it("list handles empty result", async () => {
    vi.mocked(invoke).mockResolvedValueOnce([]);

    await expect(MarketplacesService.list()).resolves.toEqual([]);
  });

  it("list handles errors", async () => {
    vi.mocked(invoke).mockRejectedValueOnce(new Error("Failed to load"));

    await expect(MarketplacesService.list()).rejects.toThrow("Failed to load");
  });

  it("update handles errors", async () => {
    vi.mocked(invoke).mockRejectedValueOnce(new Error("Update failed"));

    await expect(MarketplacesService.update("test")).rejects.toThrow("Update failed");
  });
});

