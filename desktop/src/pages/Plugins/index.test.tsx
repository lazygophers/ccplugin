import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Plugins from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

const installMock = vi.fn();
const uninstallMock = vi.fn();
let progressValue: any = null;

vi.mock("@/hooks/usePythonCommand", () => ({
  usePythonCommand: () => ({
    install: installMock,
    uninstall: uninstallMock,
    progress: progressValue,
  }),
}));

describe("Plugins page", () => {
  beforeEach(() => {
    installMock.mockReset();
    uninstallMock.mockReset();
    progressValue = null;
    // Reset but re-apply default mocks
    vi.mocked(invoke).mockReset();
    // Re-apply default mocks for Tauri commands
    vi.mocked(invoke).mockImplementation((cmd: string) => {
      if (cmd === 'get_marketplaces') {
        return Promise.resolve([]);
      }
      if (cmd === 'get_marketplace_plugins') {
        return Promise.resolve([]);
      }
      return Promise.resolve(undefined);
    });
  });

  it("renders plugins and supports search params sync", async () => {
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins?q=python"],
    });

    const input = await screen.findByRole("textbox", { name: "搜索插件" });
    expect(input).toHaveValue("python");
    // Find the plugin card by role heading
    expect(await screen.findByRole("heading", { name: "python" })).toBeInTheDocument();
  });

  it("supports installed filter", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins"],
    });

    // Wait for plugins to load
    await screen.findByRole("heading", { name: "git" });
    // Click the filter badge (not the plugin card button)
    const filterBadges = screen.getAllByRole("button", { name: "已安装" });
    await user.click(filterBadges[0]);  // Click the first one (filter badge)
    // git should not be visible when filtering by installed
    expect(screen.queryByRole("heading", { name: "git" })).not.toBeInTheDocument();
    // python should be visible as it's installed
    expect(await screen.findByRole("heading", { name: "python" })).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    vi.mocked(invoke).mockImplementationOnce(() => new Promise(() => {}));
    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins"],
    });
    expect(screen.getByText("加载插件列表...")).toBeInTheDocument();
  });

  it("shows error state and allows retry", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockRejectedValueOnce(new Error("boom")).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins"],
    });

    expect(await screen.findByText("加载失败")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("handles install and refresh", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    installMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins"],
    });

    await screen.findByRole("heading", { name: "git" });
    // Click the install button (aria-label is "安装 git")
    await user.click(screen.getByRole("button", { name: "安装 git" }));
    expect(installMock).toHaveBeenCalledWith("git");
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("handles uninstall and refresh", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValueOnce(true);
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    uninstallMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/plugins", element: <Plugins /> }], {
      initialEntries: ["/plugins"],
    });

    // Find the python plugin card by heading
    const pythonHeading = await screen.findByRole("heading", { name: "python" });
    const card = pythonHeading.closest('[role="article"]');
    expect(card).toBeTruthy();
    await user.click(within(card as HTMLElement).getByRole("button", { name: /卸载/ }));
    expect(confirmSpy).toHaveBeenCalled();
    expect(uninstallMock).toHaveBeenCalledWith("python");
    expect(invoke).toHaveBeenCalledTimes(2);
    confirmSpy.mockRestore();
  });
});

