#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Tuple


def increment_version(version_str: str) -> str:
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version_str}")
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    patch += 1
    
    return f"{major}.{minor}.{patch}"


def update_marketplace_json(marketplace_path: Path) -> Tuple[str, str]:
    with open(marketplace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    old_version = data['metadata']['version']
    new_version = increment_version(old_version)
    
    data['metadata']['version'] = new_version
    
    for plugin in data['plugins']:
        plugin['version'] = new_version
    
    with open(marketplace_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    
    return old_version, new_version


def update_plugin_versions(plugins_dir: Path, new_version: str) -> list:
    updated_plugins = []
    
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        
        plugin_json_path = plugin_dir / '.claude-plugin' / 'plugin.json'
        if not plugin_json_path.exists():
            continue
        
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            plugin_data = json.load(f)
        
        plugin_data['version'] = new_version
        
        with open(plugin_json_path, 'w', encoding='utf-8') as f:
            json.dump(plugin_data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        
        updated_plugins.append(plugin_dir.name)
    
    return updated_plugins


def main():
    base_dir = Path(__file__).parent.parent
    marketplace_path = base_dir / '.claude-plugin' / 'marketplace.json'
    plugins_dir = base_dir / 'plugins'
    
    if not marketplace_path.exists():
        print(f"Error: marketplace.json not found at {marketplace_path}")
        return 1
    
    print("Updating versions...")
    
    old_version, new_version = update_marketplace_json(marketplace_path)
    print(f"  marketplace.json: {old_version} -> {new_version}")
    
    updated_plugins = update_plugin_versions(plugins_dir, new_version)
    print(f"  Updated {len(updated_plugins)} plugin(s):")
    for plugin_name in updated_plugins:
        print(f"    - {plugin_name}: {old_version} -> {new_version}")
    
    print(f"\nVersion update completed: {old_version} -> {new_version}")
    return 0


if __name__ == '__main__':
    exit(main())
