import { describe, it, expect, vi } from "vitest";
import { invoke } from "@tauri-apps/api/core";
import { MarketplaceService } from "./marketplace-service";

describe("MarketplaceService", () => {
  describe("getAllPlugins", () => {
    it("transforms data with installed scope and path", async () => {
      const mock = [
        {
          name: "python",
          version: "1.0.0",
          installed_scope: "project",
          installed_path: "/path/to/project",
          installed_version: "0.9.0",
        },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      const expected = [
        {
          name: "python",
          version: "1.0.0",
          installed_version: "0.9.0",
          installed_scopes: ["project"],
          installed_info: [
            { scope: "project", version: "0.9.0", path: "/path/to/project" },
          ],
        },
      ];
      await expect(MarketplaceService.getAllPlugins()).resolves.toEqual(expected);
    });

    it("transforms data with user scope", async () => {
      const mock = [
        {
          name: "git",
          version: "2.0.0",
          installed_scope: "user",
          installed_path: null,
        },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      const expected = [
        {
          name: "git",
          version: "2.0.0",
          installed_scopes: ["user"],
          installed_info: [{ scope: "user", version: "2.0.0" }],
        },
      ];
      await expect(MarketplaceService.getAllPlugins()).resolves.toEqual(expected);
    });

    it("handles empty plugin list", async () => {
      vi.mocked(invoke).mockResolvedValueOnce([]);
      await expect(MarketplaceService.getAllPlugins()).resolves.toEqual([]);
    });
  });

  describe("searchPlugins", () => {
    it("transforms search results with project scope (includes path)", async () => {
      const mock = [
        {
          name: "python",
          version: "1.0.0",
          installed_scope: "project",
          installed_path: "/custom/path",
        },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      const expected = [
        {
          name: "python",
          version: "1.0.0",
          installed_scopes: ["project"],
          installed_info: [{ scope: "project", version: "1.0.0", path: "/custom/path" }],
        },
      ];
      await expect(MarketplaceService.searchPlugins("python")).resolves.toEqual(expected);
      expect(invoke).toHaveBeenCalledWith("search_plugins", { query: "python" });
    });

    it("transforms search results with local scope (no path)", async () => {
      const mock = [
        {
          name: "python",
          version: "1.0.0",
          installed_scope: "local",
          installed_path: "/custom/path",
        },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      const expected = [
        {
          name: "python",
          version: "1.0.0",
          installed_scopes: ["local"],
          installed_info: [{ scope: "local", version: "1.0.0", path: undefined }],
        },
      ];
      await expect(MarketplaceService.searchPlugins("python")).resolves.toEqual(expected);
    });

    it("handles empty search results", async () => {
      vi.mocked(invoke).mockResolvedValueOnce([]);
      await expect(MarketplaceService.searchPlugins("test")).resolves.toEqual([]);
    });
  });

  describe("filterByCategory", () => {
    it("transforms category filter results with installed scope", async () => {
      const mock = [
        {
          name: "python",
          version: "1.2.0",
          installed_scope: "project",
          installed_path: "/myproject",
          installed_version: "1.0.0",
        },
      ];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      const expected = [
        {
          name: "python",
          version: "1.2.0",
          installed_version: "1.0.0",
          installed_scopes: ["project"],
          installed_info: [
            { scope: "project", version: "1.0.0", path: "/myproject" },
          ],
        },
      ];
      await expect(MarketplaceService.filterByCategory("languages")).resolves.toEqual(expected);
      expect(invoke).toHaveBeenCalledWith("filter_plugins_by_category", { category: "languages" });
    });

    it("handles empty category results", async () => {
      vi.mocked(invoke).mockResolvedValueOnce([]);
      await expect(MarketplaceService.filterByCategory("tools")).resolves.toEqual([]);
    });
  });

  describe("getInstalledPlugins", () => {
    it("returns list of installed plugin names", async () => {
      const mock = ["python", "git"];
      vi.mocked(invoke).mockResolvedValueOnce(mock);
      await expect(MarketplaceService.getInstalledPlugins()).resolves.toEqual(mock);
      expect(invoke).toHaveBeenCalledWith("get_installed_plugins");
    });

    it("handles empty installed list", async () => {
      vi.mocked(invoke).mockResolvedValueOnce([]);
      await expect(MarketplaceService.getInstalledPlugins()).resolves.toEqual([]);
    });
  });

  describe("Error Handling", () => {
    it("handles getAllPlugins errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Fetch failed"));
      await expect(MarketplaceService.getAllPlugins()).rejects.toThrow("Fetch failed");
    });

    it("handles searchPlugins errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Search failed"));
      await expect(MarketplaceService.searchPlugins("test")).rejects.toThrow("Search failed");
    });

    it("handles filterByCategory errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Filter failed"));
      await expect(MarketplaceService.filterByCategory("tools")).rejects.toThrow("Filter failed");
    });

    it("handles getInstalledPlugins errors", async () => {
      vi.mocked(invoke).mockRejectedValueOnce(new Error("Get installed failed"));
      await expect(MarketplaceService.getInstalledPlugins()).rejects.toThrow("Get installed failed");
    });
  });
});
