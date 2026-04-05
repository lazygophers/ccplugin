import { defineConfig } from "@wdio/allure-reporter";
import type { Options } from "@wdio/types";

export const config: Options = {
  //
  // ====================
  // Runner Configuration
  // ====================
  //
  // WebdriverIO supports running e2e tests as well as unit and component tests.
  //
  // If you want to run component tests, use the wdio-component-test-service
  runner: "local",

  //
  // ==================
  // Specify Test Files
  // ==================
  // Define which test specs should run. The pattern is relative to the
  // directory from where `wdio` was called.
  //
  specs: ["./src/e2e/**/*.spec.ts"],
  // Patterns to exclude.
  exclude: [
    // 'path/to/excluded/files'
  ],

  //
  // ============
  // Capabilities
  // ============
  // Define your capabilities here. WebdriverIO can run multiple caps at the same
  // time. Depending on the number of capabilities, WebdriverIO launches several
  // test sessions.
  //
  // For Tauri, we need to use a custom capability
  maxInstances: 1,
  capabilities: [
    {
      browserName: "chrome",
      "wdio:tauriOptions": {
        application: "./target/release/ccplugin-desktop.app", // macOS
        // For Windows: "./target/release/ccplugin-desktop.exe"
        // For Linux: "./target/release/ccplugin-desktop"
        args: ["--no-sandbox"],
      },
    },
  ],

  //
  // ===================
  // Test Configurations
  // ===================
  // Define all options that are relevant for the WebdriverIO instance here
  //
  logLevel: "info",
  bail: 0,
  waitforTimeout: 10000,
  connectionRetryTimeout: 120000,
  framework: "mocha",

  //
  // ======================
  // Test Runner Options
  // ======================
  // Options for Mocha
  //
  mochaOpts: {
    ui: "bdd",
    timeout: 60000,
  },

  //
  // =================
  // Service Setup
  // =================
  // WebdriverIO supports services like Selenium Standalone, Appium or Chrome
  // Driver.
  //
  services: [
    [
      "tauri",
      {
        // Tauri driver options
      },
    ],
  ],

  //
  // ====================
  // Reporter Setup
  // ====================
  // The reporter is used to customize the report output
  //
  reporters: ["spec"],

  //
  // =====
  // Hooks
  // =====
  // WebdriverIO has several hooks you can use to interfere with the test process.
  //
  before: async function () {
    // Initialize application state before tests
  },

  afterTest: async function (
    test: {
      title: string;
      parent?: string;
    },
    context: {
      error?: Error;
      result?: number;
      duration?: number;
      passed: boolean;
      retries?: number;
    },
    results: {
      error?: Error;
      result?: number;
      duration?: number;
      passed: boolean;
      retries?: number;
    }
  ) {
    // Log test results
  },
};
