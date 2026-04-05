import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { render } from "@testing-library/react";
import Sidebar from "./Sidebar";
import { getVersion } from "@tauri-apps/api/app";

function renderSidebar(pathname = "/") {
  const router = createMemoryRouter(
    [
      {
        path: "*",
        element: <Sidebar />,
      },
    ],
    { initialEntries: [pathname] }
  );
  return render(<RouterProvider router={router} />);
}

describe("Sidebar", () => {
  beforeEach(() => {
    vi.mocked(getVersion).mockResolvedValue("0.1.0");
  });

  it("renders navigation links", () => {
    renderSidebar("/marketplaces");
    // "插件市场" is now a parent item, not a direct link
    expect(screen.getByText("插件市场")).toBeInTheDocument();
    // "设置" is a clickable div, not a link
    expect(screen.getByText("设置")).toBeInTheDocument();
    // Child items are actual links
    expect(screen.getByRole("link", { name: "市场列表" })).toBeInTheDocument();
  });

  it("toggles collapsed state and persists to localStorage", async () => {
    const user = userEvent.setup();
    renderSidebar("/");
    const button = screen.getByRole("button", { name: "收起侧边栏" });
    await user.click(button);
    expect(window.localStorage.getItem("ccplugin.desktop.sidebarCollapsed")).toBe("1");
  });

  it("restores collapsed state from localStorage", () => {
    window.localStorage.setItem("ccplugin.desktop.sidebarCollapsed", "1");
    renderSidebar("/");
    expect(screen.getByRole("button", { name: "展开侧边栏" })).toBeInTheDocument();
  });

  it("loads app version and handles fallback", async () => {
    renderSidebar("/");
    expect(await screen.findByText(/Version/)).toBeInTheDocument();
  });

  it("handles version load failure", async () => {
    vi.mocked(getVersion).mockRejectedValueOnce(new Error("x"));
    renderSidebar("/");
    expect(await screen.findByText("Version —")).toBeInTheDocument();
  });
});
