import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Dashboard from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

describe("Dashboard page", () => {
  beforeEach(() => {
    // Reset but re-apply default mocks
    vi.mocked(invoke).mockReset();
    // Re-apply default mocks for get_marketplaces
    vi.mocked(invoke).mockImplementation((cmd: string) => {
      if (cmd === 'get_marketplaces') {
        return Promise.resolve([]);
      }
      return Promise.resolve(undefined);
    });
  });

  it("renders stats and update hint", async () => {
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/", element: <Dashboard /> }]);

    expect(await screen.findByText("仪表板")).toBeInTheDocument();
    expect(screen.getByText("插件市场")).toBeInTheDocument();
    expect(screen.getByText("可更新")).toBeInTheDocument();
    expect(await screen.findByText("建议尽快更新")).toBeInTheDocument();
  });

  it("shows error card when load fails", async () => {
    vi.mocked(invoke).mockRejectedValueOnce(new Error("bad"));
    renderWithRouter([{ path: "/", element: <Dashboard /> }]);

    expect(await screen.findByText("加载失败")).toBeInTheDocument();
    expect(screen.getByText("bad")).toBeInTheDocument();
  });

  it("refresh button reloads plugins", async () => {
    const user = userEvent.setup();
    // Set up mocks:
    // 1. get_marketplaces (initial load, runs once on mount)
    // 2. get_marketplace_plugins (initial load)
    // 3. get_marketplace_plugins (refresh)
    vi.mocked(invoke)
      .mockResolvedValueOnce([])  // get_marketplaces (only on mount, not on refresh)
      .mockResolvedValueOnce(pluginFixtures)  // get_marketplace_plugins (initial load)
      .mockResolvedValueOnce(pluginFixtures);  // get_marketplace_plugins (refresh)

    renderWithRouter([{ path: "/", element: <Dashboard /> }]);

    await screen.findByText("插件市场");
    await user.click(screen.getByRole("button", { name: "刷新" }));
    // get_marketplaces is only called on mount (1), get_marketplace_plugins is called twice (initial + refresh)
    expect(invoke).toHaveBeenCalledTimes(3);
  });
});

