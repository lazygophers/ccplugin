import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { invoke } from "@tauri-apps/api/core";
import Marketplaces from "./index";
import { renderWithRouter } from "@/test/render";

describe("Marketplaces page", () => {
  beforeEach(() => {
    vi.mocked(invoke).mockReset();
  });

  it("shows loading state initially", () => {
    vi.mocked(invoke).mockImplementation(() => new Promise(() => {}));
    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });

    const loadingText = screen.queryByText(/加载/);
    expect(loadingText).toBeInTheDocument();
  });

  it("renders marketplaces list", async () => {
    vi.mocked(invoke)
      .mockResolvedValueOnce([
        {
          name: "ccplugin-market",
          url: "https://example.com/x.git",
          installLocation: "/tmp/x",
          plugins: [],
        },
      ])
      .mockResolvedValueOnce([]);

    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });

    await expect(
      screen.findByRole("heading", { name: "ccplugin-market" })
    ).resolves.toBeInTheDocument();
  });

  it("shows empty state when no marketplaces", async () => {
    vi.mocked(invoke)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });

    await expect(screen.findByText(/暂无已配置市场/)).resolves.toBeInTheDocument();
  });
});
