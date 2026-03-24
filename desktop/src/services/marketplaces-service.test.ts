import { describe, it, expect, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { MarketplacesService } from "./marketplaces-service";

describe("MarketplacesService", () => {
  it("list invokes get_marketplaces", async () => {
    const mock = [{ name: "ccplugin-market", url: "x", source: "y", installLocation: "z" }];
    vi.mocked(invoke).mockResolvedValueOnce(mock);

    await expect(MarketplacesService.list()).resolves.toEqual(mock);
    expect(invoke).toHaveBeenCalledWith("get_marketplaces");
  });
});

