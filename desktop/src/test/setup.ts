import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import { invoke } from '@tauri-apps/api/core';

// Ensure stable localStorage API in test environment
const storage = new Map<string, string>();
const localStorageMock = {
	getItem: (key: string) => (storage.has(key) ? storage.get(key)! : null),
	setItem: (key: string, value: string) => {
		storage.set(key, String(value));
	},
	removeItem: (key: string) => {
		storage.delete(key);
	},
	clear: () => {
		storage.clear();
	},
};

Object.defineProperty(globalThis, "localStorage", {
	value: localStorageMock,
	configurable: true,
});
Object.defineProperty(window, "localStorage", {
	value: localStorageMock,
	configurable: true,
});

// Mock Tauri APIs
vi.mock('@tauri-apps/api/core', () => ({
	invoke: vi.fn(),
}));

vi.mock('@tauri-apps/api/event', () => ({
	listen: vi.fn(() => Promise.resolve(vi.fn())),
	emit: vi.fn(),
}));

vi.mock('@tauri-apps/api/app', () => ({
	getName: vi.fn(() => Promise.resolve('ccplugin-desktop')),
	getVersion: vi.fn(() => Promise.resolve('0.1.0')),
}));

vi.mock('@tauri-apps/api/window', () => ({
	getCurrentWindow: vi.fn(() => ({
		show: vi.fn(() => Promise.resolve()),
		setFocus: vi.fn(() => Promise.resolve()),
	})),
}));

// Mock Tauri commands with default values
const mockInvoke = invoke as ReturnType<typeof vi.fn>;

// Set up default mock implementations
mockInvoke.mockImplementation((cmd: string, args?: unknown) => {
	switch (cmd) {
		// Plugin commands
		case 'get_marketplace_plugins':
			return Promise.resolve([]);
		case 'get_installed_plugins':
			return Promise.resolve([]);
		case 'get_marketplaces':
			return Promise.resolve([]);
		case 'update_marketplace':
			return Promise.resolve('Updated');
		case 'search_plugins':
			return Promise.resolve([]);
		case 'filter_plugins_by_category':
			return Promise.resolve([]);
		case 'install_plugin':
			return Promise.resolve(undefined);
		case 'uninstall_plugin':
			return Promise.resolve(undefined);

		// Notification commands
		case 'get_notifications':
			return Promise.resolve([]);
		case 'get_unread_count':
			return Promise.resolve(0);
		case 'add_notification':
			return Promise.resolve({
				id: 'test-id',
				type: 'info',
				title: args ? (args as any).title : 'Test',
				message: 'Test message',
				read: false,
				created_at: Date.now() / 1000,
				updated_at: Date.now() / 1000,
			});
		case 'mark_notification_read':
			return Promise.resolve(true);
		case 'mark_all_notifications_read':
			return Promise.resolve(undefined);
		case 'update_notification':
			return Promise.resolve(true);
		case 'delete_notification':
			return Promise.resolve(true);
		case 'clear_all_notifications':
			return Promise.resolve(undefined);
		case 'send_system_notification':
			return Promise.resolve(undefined);

		// Proxy commands
		case 'load_proxy_config':
			return Promise.resolve({
				enabled: false,
				http: '',
				https: '',
				noProxy: 'localhost,127.0.0.1',
			});
		case 'save_proxy_config':
			return Promise.resolve(undefined);

		default:
			console.warn(`Unhandled Tauri command mock: ${cmd}`);
			return Promise.resolve(undefined);
	}
});

// Clean up after each test
afterEach(() => {
	cleanup();
	vi.clearAllMocks();
});
