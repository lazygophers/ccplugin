import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Dashboard from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

describe("Dashboard page", () => {
  beforeEach(() => {
    vi.mocked(invoke).mockReset();
  });

  it("renders stats and update hint", async () => {
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/", element: <Dashboard /> }]);

    expect(await screen.findByText("仪表板")).toBeInTheDocument();
    expect(screen.getByText("市场插件")).toBeInTheDocument();
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
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/", element: <Dashboard /> }]);

    await screen.findByText("市场插件");
    await user.click(screen.getByRole("button", { name: "刷新" }));
    expect(invoke).toHaveBeenCalledTimes(2);
  });
});

