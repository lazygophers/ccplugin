import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { invoke } from "@tauri-apps/api/core";
import Updates from "./index";
import { renderWithRouter } from "@/test/render";
import { pluginFixtures } from "@/test/fixtures";

const updateMock = vi.fn();

vi.mock("@/hooks/usePythonCommand", () => ({
  usePythonCommand: () => ({
    update: updateMock,
  }),
}));

describe("Updates page", () => {
  beforeEach(() => {
    updateMock.mockReset();
    vi.mocked(invoke).mockReset();
  });

  it("shows empty state when no updates", async () => {
    const allLatest = pluginFixtures.map((p) =>
      p.installed ? { ...p, installed_version: p.version } : p
    );
    vi.mocked(invoke).mockResolvedValueOnce(allLatest);
    renderWithRouter([{ path: "/updates", element: <Updates /> }], {
      initialEntries: ["/updates"],
    });

    expect(await screen.findByText("一切已是最新")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "全部更新" })).toBeDisabled();
  });

  it("renders updatable plugins and supports update all", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockResolvedValueOnce(pluginFixtures).mockResolvedValueOnce(pluginFixtures);
    updateMock.mockResolvedValueOnce(undefined);

    renderWithRouter([{ path: "/updates", element: <Updates /> }], {
      initialEntries: ["/updates"],
    });

    expect(await screen.findByRole("heading", { name: "python" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "全部更新" }));
    expect(updateMock).toHaveBeenCalledWith("python");
    expect(invoke).toHaveBeenCalledTimes(2);
  });

  it("shows error state and allows retry", async () => {
    const user = userEvent.setup();
    vi.mocked(invoke).mockRejectedValueOnce(new Error("err")).mockResolvedValueOnce(pluginFixtures);
    renderWithRouter([{ path: "/updates", element: <Updates /> }], {
      initialEntries: ["/updates"],
    });

    expect(await screen.findByText("加载失败")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "重试" }));
    expect(invoke).toHaveBeenCalledTimes(2);
  });
});
