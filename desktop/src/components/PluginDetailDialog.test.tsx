import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  PluginDetailDialog,
  buildFallbackReadme,
  buildGithubRawReadmeUrl,
} from "./PluginDetailDialog";
import { pluginFixtures } from "@/test/fixtures";

describe("PluginDetailDialog helpers", () => {
  it("buildGithubRawReadmeUrl converts github tree URL", () => {
    const url = buildGithubRawReadmeUrl(
      "https://github.com/lazygophers/ccplugin/tree/master/plugins/languages/python"
    );
    expect(url).toBe(
      "https://raw.githubusercontent.com/lazygophers/ccplugin/master/plugins/languages/python/README.md"
    );
  });

  it("buildGithubRawReadmeUrl returns null for non-tree URL", () => {
    expect(buildGithubRawReadmeUrl("https://github.com/lazygophers/ccplugin")).toBeNull();
  });

  it("buildGithubRawReadmeUrl returns null for invalid URL", () => {
    expect(buildGithubRawReadmeUrl("::::")).toBeNull();
  });

  it("buildFallbackReadme includes key metadata", () => {
    const text = buildFallbackReadme(pluginFixtures[0]);
    expect(text).toContain("# python");
    expect(text).toContain("claude plugin install python");
    expect(text).toContain("AGPL-3.0-or-later");
  });
});

describe("PluginDetailDialog", () => {
  it("returns null when plugin is null", () => {
    const { container } = render(
      <PluginDetailDialog plugin={null} open onOpenChange={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("loads remote README when fetch succeeds", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      text: async () => "# Remote Readme",
    } as Response);

    render(
      <PluginDetailDialog plugin={pluginFixtures[0]} open onOpenChange={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Remote Readme")).toBeInTheDocument();
    });
  });

  it("does not fetch when dialog is closed", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");
    render(
      <PluginDetailDialog
        plugin={pluginFixtures[0]}
        open={false}
        onOpenChange={vi.fn()}
      />
    );
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("falls back to generated README when fetch fails", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 404,
      text: async () => "",
    } as Response);

    render(
      <PluginDetailDialog plugin={pluginFixtures[0]} open onOpenChange={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("无法加载远程文档")).toBeInTheDocument();
      expect(screen.getByText("安装")).toBeInTheDocument();
    });
  });

  it("calls onInstall when install button clicked", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      text: async () => "# x",
    } as Response);

    const user = userEvent.setup();
    const onInstall = vi.fn();
    render(
      <PluginDetailDialog
        plugin={pluginFixtures[1]}
        open
        onOpenChange={vi.fn()}
        onInstall={onInstall}
      />
    );

    await user.click(screen.getByRole("button", { name: "安装插件" }));
    expect(onInstall).toHaveBeenCalledWith("git");
  });

  it("shows installed badge for installed plugin", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      text: async () => "# x",
    } as Response);

    render(
      <PluginDetailDialog plugin={pluginFixtures[2]} open onOpenChange={vi.fn()} />
    );

    expect(await screen.findByText(/已安装 v1.0.0/)).toBeInTheDocument();
  });

  it("calls onUninstall when uninstall button clicked", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      text: async () => "# x",
    } as Response);

    const user = userEvent.setup();
    const onUninstall = vi.fn();
    render(
      <PluginDetailDialog
        plugin={pluginFixtures[0]}
        open
        onOpenChange={vi.fn()}
        onUninstall={onUninstall}
      />
    );

    const uninstallButton = await screen.findByRole("button", { name: "卸载 python" });
    await user.click(uninstallButton);
    expect(onUninstall).toHaveBeenCalledWith("python");
  });
});
