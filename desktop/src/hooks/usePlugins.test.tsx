import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { usePlugins } from "./usePlugins";

vi.mock("@/services/marketplace-service", () => ({
  MarketplaceService: {
    getAllPlugins: vi.fn(),
  },
}));

import { MarketplaceService } from "@/services/marketplace-service";
import { pluginFixtures } from "@/test/fixtures";

describe("usePlugins", () => {
  it("loads plugins successfully", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockResolvedValueOnce(pluginFixtures);

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeNull();
    expect(result.current.plugins.length).toBe(pluginFixtures.length);
  });

  it("sets error when load fails", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockRejectedValueOnce(new Error("nope"));

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.plugins).toEqual([]);
    expect(result.current.error).toBe("nope");
  });

  it("normalizes non-Error rejection to string", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockRejectedValueOnce("x");

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe("x");
  });

  it("normalizes invalid backend data to empty list", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockResolvedValueOnce(undefined as never);

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeNull();
    expect(result.current.plugins).toEqual([]);
    expect(result.current.filteredPlugins).toEqual([]);
  });

  it("filters by keyword and search", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockResolvedValueOnce(pluginFixtures);

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setSelectedKeyword("git");
    });
    expect(result.current.filteredPlugins.map((p) => p.name)).toEqual(["git"]);

    act(() => {
      result.current.setSelectedKeyword(null);
      result.current.setSearchQuery("python");
    });
    expect(result.current.filteredPlugins.map((p) => p.name)).toEqual(["python"]);
  });

  it("filters by installed state", async () => {
    vi.mocked(MarketplaceService.getAllPlugins).mockResolvedValueOnce(pluginFixtures);

    const { result } = renderHook(() => usePlugins());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.setInstalledFilter("installed");
    });
    expect(result.current.filteredPlugins.map((p) => p.name).sort()).toEqual(["docx", "python"]);

    act(() => {
      result.current.setInstalledFilter("uninstalled");
    });
    expect(result.current.filteredPlugins.map((p) => p.name)).toEqual(["git"]);
  });
});
