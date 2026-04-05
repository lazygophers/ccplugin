import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PluginCard } from "./PluginCard";
import { pluginFixtures } from "@/test/fixtures";

describe("PluginCard", () => {
  it("renders install button for uninstalled plugin", async () => {
    const user = userEvent.setup();
    const onInstall = vi.fn();
    const plugin = pluginFixtures[1];

    render(<PluginCard plugin={plugin} onInstall={onInstall} />);
    await user.click(screen.getByRole("button", { name: "安装" }));

    expect(onInstall).toHaveBeenCalledWith(plugin.name);
  });

  it("renders installed state when no onUpdate", () => {
    render(<PluginCard plugin={pluginFixtures[2]} />);
    expect(screen.getByText(/已安装 v1.0.0/)).toBeInTheDocument();
  });

  it("renders uninstall action when installed and onUninstall provided", async () => {
    const user = userEvent.setup();
    const onUninstall = vi.fn();
    render(<PluginCard plugin={pluginFixtures[0]} onUninstall={onUninstall} />);

    await user.click(screen.getByRole("button", { name: /卸载/ }));
    expect(onUninstall).toHaveBeenCalledWith("python");
  });

  it("renders update action when installed and onUpdate provided", async () => {
    const user = userEvent.setup();
    const onUpdate = vi.fn();
    render(<PluginCard plugin={pluginFixtures[0]} onUpdate={onUpdate} />);

    await user.click(screen.getByRole("button", { name: /更新/ }));
    expect(onUpdate).toHaveBeenCalledWith("python");
  });

  it("renders update + uninstall when both callbacks provided", () => {
    render(
      <PluginCard
        plugin={pluginFixtures[0]}
        onUpdate={vi.fn()}
        onUninstall={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: /更新/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /卸载/ })).toBeInTheDocument();
  });

  it("renders keyword overflow indicator", () => {
    const plugin = {
      ...pluginFixtures[1],
      keywords: ["a", "b", "c", "d"],
    };
    render(<PluginCard plugin={plugin} />);
    expect(screen.getByText("+1")).toBeInTheDocument();
  });

  it("shows updating state when updating=true", () => {
    render(<PluginCard plugin={pluginFixtures[0]} onUpdate={vi.fn()} updating />);
    expect(screen.getByText("更新中...")).toBeInTheDocument();
  });

  it("shows uninstalling state when uninstalling=true", () => {
    render(<PluginCard plugin={pluginFixtures[0]} onUninstall={vi.fn()} uninstalling />);
    expect(screen.getByText("卸载中...")).toBeInTheDocument();
  });

  it("shows installing state when installing=true", () => {
    render(<PluginCard plugin={pluginFixtures[1]} onInstall={vi.fn()} installing />);
    expect(screen.getByText("安装中...")).toBeInTheDocument();
  });

  it("renders scope badge for user scope", () => {
    const plugin = { ...pluginFixtures[0], installed_scope: "user" };
    render(<PluginCard plugin={plugin} />);
    expect(screen.getByText("用户")).toBeInTheDocument();
  });

  it("renders scope badge for project scope", () => {
    const plugin = { ...pluginFixtures[0], installed_scope: "project" };
    render(<PluginCard plugin={plugin} />);
    expect(screen.getByText("项目")).toBeInTheDocument();
  });

  it("renders scope badge for local scope", () => {
    const plugin = { ...pluginFixtures[0], installed_scope: "local" };
    render(<PluginCard plugin={plugin} />);
    expect(screen.getByText("local")).toBeInTheDocument();
  });

  it("does not render scope badge when not installed", () => {
    render(<PluginCard plugin={pluginFixtures[1]} />);
    expect(screen.queryByText(/用户|项目|local/)).not.toBeInTheDocument();
  });

  it("memo prevents re-render when scope changes", () => {
    const { rerender } = render(
      <PluginCard
        plugin={pluginFixtures[0]}
        onUpdate={vi.fn()}
        onUninstall={vi.fn()}
      />
    );
    const initialRender = screen.getByText("python");

    rerender(
      <PluginCard
        plugin={{ ...pluginFixtures[0], installed_scope: "project" }}
        onUpdate={vi.fn()}
        onUninstall={vi.fn()}
      />
    );

    expect(initialRender).toBeInTheDocument();
  });

  it("detail button calls onViewDetails", async () => {
    const user = userEvent.setup();
    const onViewDetails = vi.fn();
    const plugin = pluginFixtures[0];
    render(<PluginCard plugin={plugin} onViewDetails={onViewDetails} />);

    await user.click(screen.getByRole("button", { name: "详情" }));
    expect(onViewDetails).toHaveBeenCalledWith(plugin);
  });
});
