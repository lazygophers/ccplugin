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
    vi.mocked(invoke).mockImplementationOnce(() => new Promise(() => {}));
    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });
    expect(screen.getByText("加载市场列表...")).toBeInTheDocument();
  });

  it("renders marketplaces list", async () => {
    vi.mocked(invoke).mockResolvedValueOnce([
      { name: "ccplugin-market", url: "https://example.com/x.git", installLocation: "/tmp/x" },
    ]);
    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });

    expect(await screen.findByRole("heading", { name: "ccplugin-market" })).toBeInTheDocument();
    expect(screen.getByText(/安装位置：\/tmp\/x/)).toBeInTheDocument();
  });

  it("shows empty state", async () => {
    vi.mocked(invoke).mockResolvedValueOnce([]);
    renderWithRouter([{ path: "/marketplaces", element: <Marketplaces /> }], {
      initialEntries: ["/marketplaces"],
    });

    expect(await screen.findByText("暂无已配置市场")).toBeInTheDocument();
  });
});

