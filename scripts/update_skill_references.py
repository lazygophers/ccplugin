#!/usr/bin/env python3
"""
更新所有对重命名的 skills 的引用
"""
import os
import re

# 需要替换的映射：旧名称 -> 新名称
SKILL_RENAMES = {
    'plugin-organization': 'plugin-organization-skills',
    'python-script-organization': 'python-script-organization-skills',
    'fasthttp': 'fasthttp-skills',
    'gin': 'gin-skills',
    'gozero': 'gozero-skills',
    'gofiber': 'gofiber-skills',
    'gorm-gen': 'gorm-gen-skills',
    'gorm': 'gorm-skills',
    'lrpc-anyx': 'lrpc-anyx-skills',
    'lrpc-app': 'lrpc-app-skills',
    'lrpc-candy': 'lrpc-candy-skills',
    'lrpc-config': 'lrpc-config-skills',
    'lrpc-core': 'lrpc-core-skills',
    'lrpc-cryptox': 'lrpc-cryptox-skills',
    'lrpc-database': 'lrpc-database-skills',
    'lrpc-defaults': 'lrpc-defaults-skills',
    'lrpc-human': 'lrpc-human-skills',
    'lrpc-hystrix': 'lrpc-hystrix-skills',
    'lrpc-i18n': 'lrpc-i18n-skills',
    'lrpc-json': 'lrpc-json-skills',
    'lrpc-log': 'lrpc-log-skills',
    'lrpc-mongo': 'lrpc-mongo-skills',
    'lrpc-network': 'lrpc-network-skills',
    'lrpc-osx': 'lrpc-osx-skills',
    'lrpc-queue': 'lrpc-queue-skills',
    'lrpc-randx': 'lrpc-randx-skills',
    'lrpc-redis-cache': 'lrpc-redis-cache-skills',
    'lrpc-routine': 'lrpc-routine-skills',
    'lrpc-runtime': 'lrpc-runtime-skills',
    'lrpc-string': 'lrpc-string-skills',
    'lrpc-utils-cache': 'lrpc-utils-cache-skills',
    'lrpc-validator': 'lrpc-validator-skills',
    'lrpc-wait': 'lrpc-wait-skills',
    'lrpc-xerror': 'lrpc-xerror-skills',
    'lrpc-xtime': 'lrpc-xtime-skills',
    'antd': 'antd-skills',
    'nextjs': 'nextjs-skills',
    'react': 'react-skills',
    'vue': 'vue-skills',
    'flutter': 'flutter-skills',
    'flutter-android': 'flutter-android-skills',
    'flutter-ios': 'flutter-ios-skills',
    'flutter-linux': 'flutter-linux-skills',
    'flutter-macos': 'flutter-macos-skills',
    'flutter-web': 'flutter-web-skills',
    'flutter-windows': 'flutter-windows-skills',
    'golang': 'golang-skills',
    'gtpl': 'gtpl-skills',
    'javascript': 'javascript-skills',
    'naming': 'naming-skills',
    'python': 'python-skills',
    'typescript': 'typescript-skills',
    'llms': 'llms-skills',
    'task': 'task-skills',
    'skill-name': 'skill-name-skills',
    'brutalism': 'brutalism-skills',
    'style-dark': 'style-dark-skills',
    'glassmorphism': 'glassmorphism-skills',
    'gradient': 'gradient-skills',
    'style-healing': 'style-healing-skills',
    'high-contrast': 'high-contrast-skills',
    'luxe': 'luxe-skills',
    'minimal': 'minimal-skills',
    'neon': 'neon-skills',
    'neumorphism': 'neumorphism-skills',
    'pastel': 'pastel-skills',
    'retro': 'retro-skills',
    'vibrant': 'vibrant-skills',
    'citation-validator': 'citation-validator-skills',
    'content-retriever': 'content-retriever-skills',
    'explorer': 'explorer-skills',
    'github-analysis': 'github-analysis-skills',
    'got-controller': 'got-controller-skills',
    'question-refiner': 'question-refiner-skills',
    'research-executor': 'research-executor-skills',
    'synthesizer': 'synthesizer-skills',
    'git': 'git-skills',
    'semantic': 'semantic-skills',
}

def update_file_references(file_path: str) -> bool:
    """更新单个文件中的所有 skill 引用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        updated_content = original_content

        for old_name, new_name in SKILL_RENAMES.items():
            # 1. 替换路径中的 skill 名称：./skills/old-name/ → ./skills/new-name/
            updated_content = updated_content.replace(
                f"./skills/{old_name}/",
                f"./skills/{new_name}/"
            )

            # 2. 替换 frontmatter 中的 skills: 字段
            # 匹配 skills: skillname（可能有空格）
            updated_content = re.sub(
                rf'^skills:\s*{re.escape(old_name)}\s*$',
                f'skills: {new_name}',
                updated_content,
                flags=re.MULTILINE
            )

            # 3. 替换列表中的 skill 名称（skills: [python, golang]）
            # 前面是空白或逗号，后面是空白、逗号或结束
            updated_content = re.sub(
                rf'([,\s[]){re.escape(old_name)}([,\s\]])',
                rf'\1{new_name}\2',
                updated_content
            )

            # 4. 替换在链接中的 skill 引用（如 [@/task:task]）
            updated_content = updated_content.replace(
                f':{old_name}',
                f':{new_name}'
            )

        if updated_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False

def main():
    """主函数"""
    root_dir = os.getcwd()
    updated_count = 0
    processed_count = 0

    print(f"Updating skill references in {root_dir}\n")

    for root, dirs, files in os.walk(root_dir):
        # 跳过某些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache']]

        for file in files:
            # 处理所有 .md 和 .json 文件，但跳过 SKILL.md 本身
            if (file.endswith(('.md', '.json')) and file != 'SKILL.md') or file == 'plugin.json':
                file_path = os.path.join(root, file)
                processed_count += 1

                if update_file_references(file_path):
                    updated_count += 1
                    print(f"✓ Updated: {file_path}")

    print("\n=== Update complete ===")
    print(f"Processed: {processed_count} files")
    print(f"Updated: {updated_count} files")

if __name__ == '__main__':
    main()
