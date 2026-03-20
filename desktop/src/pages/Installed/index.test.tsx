import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Installed from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

const updateMock = vi.fn();

vi.mock("@/hooks/usePythonCommand", () => ({
  usePythonCommand: () => ({
    update: updateMock,
  }),
}));

describe("Installed page", () => {
  beforeEach(() => {
    updateMock.mockReset();
    vi.mocked(invoke).mockReset();
  });

  it("shows loading state initially", () => {
    vi.mocked(invoke).mockImplementationOnce(() => new Promise(() => {}));
    renderWithRouter([{ path: "/installed", element: <Installed /> }], {
      initialEntries: ["/installed"],
    });
    expect(screen.getByText("加载中...")).toBeInTheDocument();
  });

  it("shows error state and allows retry", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockRejectedValueOnce(new Error("fail")).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/installed", element: <Installed /> }], {
      initialEntries: ["/installed"],
    });

    expect(await screen.findByText("加载失败")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("shows empty state when nothing installed", async () => {
    const noInstalled = pluginFixtures.map((p) => ({ ...p, installed: false, installed_version: null }));
    vi.mocked(invoke).mockResolvedValueOnce(noInstalled);
    renderWithRouter([{ path: "/installed", element: <Installed /> }], {
      initialEntries: ["/installed"],
    });

    expect(await screen.findByText("暂无已安装插件")).toBeInTheDocument();
  });

  it("updates an installed plugin", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    updateMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/installed", element: <Installed /> }], {
      initialEntries: ["/installed"],
    });

    const heading = await screen.findByRole("heading", { name: "python" });
    const card = heading.closest('[role="article"]');
    expect(card).toBeTruthy();
    await user.click(within(card as HTMLElement).getByRole("button", { name: /更新/ }));
    expect(updateMock).toHaveBeenCalledWith("python");
    expect(invoke).toHaveBeenCalledTimes(2);
  });
});
