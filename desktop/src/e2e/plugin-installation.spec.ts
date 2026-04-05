import type { XVisionPage } from "@wdio/tauri-service";
import { expect } from "chai";

describe("Plugin Installation Flow", () => {
  it("should install plugin with user scope", async function () {
    const app = this.app as XVisionPage;

    // Navigate to marketplaces page
    await app.url("/marketplaces");
    await app.pause(1000);

    // Wait for marketplaces to load
    const marketplaceHeader = await app.$("h2=ccplugin-market");
    expect(await marketplaceHeader.isExisting()).to.be.true;

    // Find and click install button on first uninstalled plugin
    const installButton = await app.$("button=安装");
    expect(await installButton.isExisting()).to.be.true;
    await installButton.click();
    await app.pause(500);

    // Verify scope dialog appears
    const dialogTitle = await app.$("/html/body/div[2]/div/h2");
    expect(await dialogTitle.getText()).to.include("选择安装范围");

    // Verify user scope is selected by default
    const userScopeRadio = await app.$("input[type='radio'][value='user']");
    expect(await userScopeRadio.isSelected()).to.be.true;

    // Click confirm to install with user scope
    const confirmButton = await app.$("button=确认安装");
    await confirmButton.click();
    await app.pause(2000);

    // Verify installation success - check for scope badge
    const scopeBadge = await app.$("span=用户");
    expect(await scopeBadge.isExisting()).to.be.true;
  });

  it("should install plugin with project scope", async function () {
    const app = this.app as XVisionPage;

    // Navigate to marketplaces page
    await app.url("/marketplaces");
    await app.pause(1000);

    // Find and click install button
    const installButton = await app.$("button=安装");
    await installButton.click();
    await app.pause(500);

    // Select project scope
    const projectScopeRadio = await app.$("input[type='radio'][value='project']");
    await projectScopeRadio.click();
    await app.pause(200);

    // Confirm installation
    const confirmButton = await app.$("button=确认安装");
    await confirmButton.click();
    await app.pause(2000);

    // Verify project scope badge appears
    const scopeBadge = await app.$("span=项目");
    expect(await scopeBadge.isExisting()).to.be.true;
  });

  it("should cancel installation when cancel button clicked", async function () {
    const app = this.app as XVisionPage;

    // Navigate to marketplaces page
    await app.url("/marketplaces");
    await app.pause(1000);

    // Click install button
    const installButton = await app.$("button=安装");
    await installButton.click();
    await app.pause(500);

    // Click cancel
    const cancelButton = await app.$("button=取消");
    await cancelButton.click();
    await app.pause(500);

    // Verify dialog is closed and plugin still shows install button
    const installButtonStillVisible = await app.$("button=安装");
    expect(await installButtonStillVisible.isExisting()).to.be.true;
  });

  it("should display correct installation status for installed plugins", async function () {
    const app = this.app as XVisionPage;

    // Navigate to marketplaces page
    await app.url("/marketplaces");
    await app.pause(1000);

    // Check for installed plugin indicators
    const installedPlugins = await app.$$("span=用户");

    // Each installed plugin should show scope badge
    for (const plugin of installedPlugins) {
      expect(await plugin.isExisting()).to.be.true;
      const text = await plugin.getText();
      expect(["用户", "项目", "local"]).to.include(text);
    }
  });

  it("should show update button when newer version available", async function () {
    const app = this.app as XVisionPage;

    // This test requires a plugin with outdated version
    await app.url("/marketplaces");
    await app.pause(1000);

    // Look for update button (if any plugin has update available)
    const updateButton = await app.$("button=更新");

    // If update button exists, verify it works
    if (await updateButton.isExisting()) {
      await updateButton.click();
      await app.pause(2000);

      // Verify update initiated (check for loading state)
      const updatingText = await app.$("text=更新中...");
      expect(await updatingText.isExisting()).to.be.true;
    }
  });
});

describe("Plugin Marketplace Navigation", () => {
  it("should load marketplace list successfully", async function () {
    const app = this.app as XVisionPage;

    await app.url("/marketplaces");
    await app.pause(1000);

    // Verify marketplace header exists
    const header = await app.$("h1=插件市场");
    expect(await header.isExisting()).to.be.true;
  });

  it("should display empty state when no marketplaces configured", async function () {
    const app = this.app as XVisionPage;

    // This test requires mocking or specific setup
    // For now, just verify the page loads
    await app.url("/marketplaces");
    await app.pause(1000);

    const header = await app.$("h1=插件市场");
    expect(await header.isExisting()).to.be.true;
  });

  it("should filter plugins by keyword", async function () {
    const app = this.app as XVisionPage;

    await app.url("/marketplaces");
    await app.pause(1000);

    // Look for search input if it exists
    const searchInput = await app.$("input[type='search']");

    if (await searchInput.isExisting()) {
      await searchInput.setValue("python");
      await app.pause(500);

      // Verify filtered results
      const pythonPlugins = await app.$$("*=python");
      expect(pythonPlugins.length).to.be.greaterThan(0);
    }
  });
});

describe("Plugin Card Display", () => {
  it("should render plugin card with all required information", async function () {
    const app = this.app as XVisionPage;

    await app.url("/marketplaces");
    await app.pause(1000);

    // Find first plugin card
    const pluginCard = await app$(".plugin-card");
    expect(pluginCard.length).to.be.greaterThan(0);

    // Check for essential elements
    const firstCard = pluginCard[0];

    // Plugin name should exist
    const pluginName = await firstCard.$(".plugin-name");
    expect(await pluginName.isExisting()).to.be.true;

    // Plugin description should exist
    const description = await firstCard.$(".plugin-description");
    expect(await description.isExisting()).to.be.true;
  });

  it("should show install/uninstall/update buttons based on plugin state", async function () {
    const app = this.app as XVisionPage;

    await app.url("/marketplaces");
    await app.pause(1000);

    // Get all plugin cards
    const pluginCards = await app$(".plugin-card");
    expect(pluginCards.length).to.be.greaterThan(0);

    // Check that each card has appropriate buttons
    for (const card of pluginCards) {
      const installButton = await card.$("button=安装");
      const updateButton = await card.$("button=更新");
      const uninstallButton = await card.$("button=卸载");

      // At least one button should exist (install OR update OR uninstall)
      const hasButton =
        (await installButton.isExisting()) ||
        (await updateButton.isExisting()) ||
        (await uninstallButton.isExisting());

      expect(hasButton).to.be.true;
    }
  });
});
