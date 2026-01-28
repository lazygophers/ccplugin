# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CCPlugin Market** is a centralized marketplace for Claude Code plugins, providing high-quality plugins and development templates for enhancing Claude Code functionality. The project is structured as a monorepo with:

- **Core library** (`lib/`): Shared utilities including logging infrastructure and helper functions
- **Plugins** (`plugins/`): Multiple plugin implementations (task management, semantic search, git operations, language-specific development support)
- **Scripts** (`scripts/`): Utility scripts for version management and cache cleanup

**Tech Stack:**
- **Python**: >= 3.12 (mandatory)
- **Package Manager**: `uv` (mandatory, not pip)
- **Key Dependencies**: pydantic, typer, rich, lancedb, fastembed, sentence-transformers
- **Version Management**: 3-part semantic versioning (major.minor.patch)

---

## Architecture & Structure

### Monorepo Layout

```
ccplugin/
├── lib/                          # Shared library (logging, utilities)
│   ├── logging/                  # Centralized logging infrastructure
│   ├── utils/                    # Utility functions
│   ├── hooks/                    # Hook system for plugins
│   └── tests/                    # Unit tests
│
├── plugins/                      # All plugin implementations
│   ├── task/                     # Task management plugin (SQLite-based)
│   ├── code/
│   │   ├── semantic/             # Semantic search plugin (vector embeddings)
│   │   ├── git/                  # Git operations plugin
│   │   ├── python/               # Python development plugin
│   │   ├── golang/               # Golang development plugin
│   │   ├── typescript/           # TypeScript development plugin
│   │   ├── javascript/           # JavaScript development plugin
│   │   ├── vue/                  # Vue 3 development plugin
│   │   ├── react/                # React 18+ development plugin
│   │   ├── nextjs/               # Next.js 16+ development plugin
│   │   ├── antd/                 # Ant Design 5.x plugin
│   │   └── flutter/              # Flutter development plugin
│   ├── notify/                   # Notification plugin
│   ├── version/                  # Version management plugin
│   ├── style/                    # Styling plugin
│   └── template/                 # Plugin development template
│
├── scripts/                      # Utility scripts
│   ├── clean.py                  # Clean old plugin versions from cache
│   └── update_version.py         # Update version across all plugins
│
├── docs/                         # Documentation
├── .claude/                      # Claude Code local configuration
│   └── skills/                   # Local skills (plugin & python script organization)
│       ├── plugin-organization/  # Plugin structure & configuration
│       └── python-script-organization/  # Python coding standards
├── .claude-plugin/               # Plugin marketplace metadata
├── pyproject.toml                # Main project configuration
└── uv.lock                       # Dependency lock file

```

### Plugin Structure (Standard for All Plugins)

Each plugin follows this structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json               # Plugin manifest (name, version, description, etc.)
├── .mcp.json                     # MCP server configuration (if applicable)
├── .lsp.json                     # LSP server configuration (if applicable)
├── commands/                     # Custom commands (.md files)
├── agents/                       # Sub-agents (.md files)
├── skills/                       # Skills definitions
│   └── skill-name/
│       └── SKILL.md               # Skill entry with frontmatter (name, description)
├── scripts/                      # Python scripts for plugin logic
│   ├── __init__.py
│   ├── main.py                   # CLI entry point (Click-based)
│   ├── hooks.py                  # Hook event handlers (optional)
│   ├── mcp.py                    # MCP server implementation (optional)
│   └── <module>.py               # Business logic modules
├── hooks/
│   └── hooks.json                # Hook event configuration
├── pyproject.toml                # Plugin-specific dependencies
├── README.md                     # Plugin documentation
└── CHANGELOG.md                  # Version history
```

**MCP Server Pattern (via main.py subcommand):**

```json
// .mcp.json - MCP server configuration
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": ["run", "${CLAUDE_PLUGIN_ROOT}/scripts/main.py", "mcp"]
    }
  }
}
```

```python
# main.py - CLI entry with MCP subcommand
@click.group()
def main(): pass

@main.command()
def mcp():
    """MCP server mode"""
    from mcp import VersionMCPServer
    asyncio.run(server.run())

# mcp.py - Async MCP server implementation
class VersionMCPServer:
    async def handle_request(self, request: dict) -> dict:
        # JSON-RPC 2.0 handler with tools/list, tools/call, initialize
```

**Skills Directory Pattern:**

```
skills/
└── python/                      # Skill name (lowercase)
    ├── SKILL.md                   # Entry file with frontmatter
    ├── subtopic.md                # Additional documentation
    └── patterns/                  # Optional subdirectory
        └── design-patterns.md
```

**SKILL.md frontmatter format:**
```markdown
---
name: python
description: Python development standards and best practices
---
```

---

## Development Commands

### Environment Setup

```bash
# Install uv (if not already installed)
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version

# Install all dependencies (uses uv.lock)
uv sync

# Activate virtual environment (if using local venv)
source .venv/bin/activate
```

### Building & Installation

```bash
# Build the main project
uv build

# Install locally for development
uv pip install -e .

# Install specific plugin (for testing)
/plugin install ./plugins/task
/plugin install ./plugins/code/semantic

# Reinstall plugin (force latest)
/plugin install ./plugins/task --force
```

### Linting & Code Quality

```bash
# Run ruff for linting (configured in pyproject.toml)
uv run ruff check .
uv run ruff format .

# Check specific directory
uv run ruff check plugins/task/scripts/
uv run ruff format plugins/task/scripts/ --check
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests for specific module
uv run pytest lib/tests/test_logging.py

# Run tests with verbose output
uv run pytest -v

# Run tests for a specific plugin
uv run pytest plugins/task/tests/

# Run tests with coverage
uv run pytest --cov=lib --cov=plugins
```

### Version Management

```bash
# Update version across all plugins and main project
# This increments patch version (x.x.N) and updates:
# - Root pyproject.toml
# - All plugin/.claude-plugin/plugin.json files
# - scripts/.version file (if exists)
uv run scripts/update_version.py

# Check current version
cat .version
```

### Cache Cleanup

```bash
# Preview old plugin versions to be deleted (no deletion)
clean --dry-run
# or
clean -d

# Actually delete old plugin versions from ~/.claude/plugins/cache/
# Keeps only the latest version of each plugin
clean

# Remote execution via uvx
uvx --from git+https://github.com/lazygophers/ccplugin clean
uvx --from git+https://github.com/lazygophers/ccplugin clean --dry-run
```

### Plugin-Specific Commands

```bash
# Task plugin - project task management
task add "Task description"
task list
task stats
/task add "Implement feature X"

# Semantic search plugin - code search with embeddings
semantic init                    # Initialize vector database
semantic index                   # Build/update code index
semantic search "how to read files"

# Git plugin - version control operations
/commit-all "feat: description"  # Commit all changes
/update-ignore                   # Update .gitignore intelligently
/create-pr                       # Create pull request

# Version plugin - version info
version --help
```

---

## Development Workflow

### Creating a New Plugin

1. **Use the template**:
   ```bash
   cp -r plugins/template plugins/my-new-plugin
   cd plugins/my-new-plugin
   ```

2. **Configure plugin metadata** in `.claude-plugin/plugin.json`:
   - Update `name`, `version`, `description`
   - Update `author`, `homepage`, `repository`, `license`
   - Define `commands`, `agents`, `skills` paths

3. **Implement plugin components**:
   - **Commands**: Create `.md` files in `commands/` directory
   - **Agents**: Create `.md` files in `agents/` directory
   - **Skills**: Create skill definitions in `skills/` directory
   - **Scripts**: Implement logic in `scripts/` directory (Python preferred)

4. **Update pyproject.toml** with dependencies

5. **Test locally**: `/plugin install ./plugins/my-new-plugin`

6. **Build & verify**: `uv build`

### Python Execution Rules (Mandatory)

**Always use `uv run` to execute Python scripts in this project:**

```bash
# ✅ Correct
uv run scripts/script.py
uv run plugins/task/scripts/main.py

# ❌ Incorrect (forbidden)
python3 scripts/script.py
python scripts/script.py
./scripts/script.py
```

**Why mandatory:**
- Ensures dependency isolation via virtual environments
- Prevents global Python environment pollution
- Guarantees version consistency across all environments
- uv provides significantly faster execution

### Shared Library (lib/)

The `lib/` directory provides shared utilities used across all plugins:

- **`lib.logging`**: Centralized logging manager with rich formatting
- **`lib.utils`**: Common utility functions (env handling, etc.)
- **`lib.hooks`**: Hook system for plugin event handling

To use shared library in plugins:
```python
from lib.logging import get_logger
from lib.utils import get_env_value
```

### Plugin Dependencies

- Plugins can depend on the shared `lib` package
- Main project dependencies are in root `pyproject.toml`
- Plugin-specific dependencies go in plugin `pyproject.toml`
- Use `uv sync` to sync all dependencies across workspace

---

## Key Technical Decisions

### 1. Monorepo with Workspace Structure
- **Why**: Simplifies shared code (logging, utilities), centralized version management, easier plugin discovery
- **Trade-off**: Requires careful namespace management to avoid conflicts

### 2. uv as Mandatory Package Manager
- **Why**: ~10x faster than pip/virtualenv, deterministic locking, built-in virtual env management
- **Impact**: All Python execution must use `uv run`

### 3. Semantic Versioning (major.minor.patch)
- **Format**: `0.0.X` (4-part with build number in .version file)
- **Update**: Use `scripts/update_version.py` to atomically update all versions

### 4. Plugin.json as Single Source of Truth
- Each plugin's metadata is centralized in `.claude-plugin/plugin.json`
- Version, commands, agents, skills paths defined here
- No need to manually track plugin locations

### 5. Shared Library for Logging
- All plugins use `lib.logging` for consistent logging behavior
- Provides rich-formatted, context-aware logging
- Located in root `lib/` directory, imported via `from lib.logging import ...`

### 6. MCP Server Support (Optional)
- Plugins can define MCP servers via `.mcp.json`
- Enables integration with Claude's Model Context Protocol
- Not required for all plugins

---

## Common Development Patterns

### Adding a New CLI Command to a Plugin

1. Create command file in `commands/` (e.g., `commands/my-command.md`)
2. Update `.claude-plugin/plugin.json` to reference the command:
   ```json
   "commands": [
     "./commands/my-command.md"
   ]
   ```
3. Command gets registered automatically when plugin is installed

### Adding a New Sub-Agent to a Plugin

1. Create agent file in `agents/` (e.g., `agents/my-agent.md`)
2. Define agent behavior in markdown frontmatter
3. Update `.claude-plugin/plugin.json`:
   ```json
   "agents": [
     "./agents/my-agent.md"
   ]
   ```

### Adding Skills to Guide Claude Code Behavior

**Plugin Skills:**
1. Create skill directory in `skills/<skill-name>/`
2. Create `SKILL.md` entry file with frontmatter:
   ```markdown
   ---
   name: skill-name
   description: Brief description
   ---
   ```
3. Skills are auto-discovered when plugin is loaded
4. Reference in plugin.json: `"skills": "./skills/"`

**Local Project Skills (.claude/skills/):**
- `plugin-organization/`: Plugin structure, plugin.json, components
- `python-script-organization/`: Python coding standards, imports, patterns
- These skills are available for all development in this repo
- Follow same SKILL.md pattern as plugin skills

---

## Important File Roles

| File | Purpose |
|------|---------|
| `pyproject.toml` | Root project config: main dependencies, workspace members, scripts |
| `uv.lock` | Dependency lock file (generated, don't edit manually) |
| `.version` | Current version number (use `scripts/update_version.py` to update) |
| `.python-version` | Required Python version (3.12+) |
| `CHANGELOG.md` | Version history and release notes |
| `LICENSE` | AGPL-3.0-or-later |
| `.claude-plugin/plugin.json` | Plugin marketplace metadata per plugin |
| `VOICE_SUPPORT.md` | Documentation for voice/audio support |

---

## Debugging Tips

### Check Plugin Installation
```bash
# List installed plugins
ls ~/.claude/plugins/

# Check plugin cache
ls ~/.claude/plugins/cache/
```

### View Plugin Manifest
```bash
# Check what a plugin exposes
cat plugins/task/.claude-plugin/plugin.json
```

### Run Specific Plugin Tests
```bash
# Test only semantic plugin
uv run pytest plugins/code/semantic/tests/ -v

# Test lib logging
uv run pytest lib/tests/test_logging.py -v
```

### Debug Python Script Issues
```bash
# Run with verbose output
uv run --verbose scripts/update_version.py

# Check uv environment
uv venv
uv python --version
```

---

## Integration with Claude Code

### Plugin Auto-Activation
Certain plugins auto-activate based on context:
- **python**: Activates when editing Python files
- **golang**: Activates when editing Go files
- **typescript/react/vue**: Activate for respective file types
- Language plugins provide coding standards and best practices

### Manual Plugin Usage
```bash
# Install plugin
/plugin install ./plugins/task

# Use plugin commands (if defined)
/task add "New task"
/semantic search "query"
```

### Plugin Data Storage
- Plugin data stored in `.lazygophers/ccplugin/<plugin-name>/`
- Auto-ignored by `.gitignore`
- Per-project isolation (not global)

---

## Maintenance

### Regular Tasks

- **Version updates**: Run `uv run scripts/update_version.py` when releasing
- **Dependency updates**: Run `uv update` periodically and commit `uv.lock`
- **Cache cleanup**: Run `clean` command occasionally to remove old plugin versions
- **Test verification**: Run `uv run pytest` before commits
- **Documentation**: Keep plugin README.md and root README.md in sync

### Common Issues

| Issue | Solution |
|-------|----------|
| "python3: command not found" | Use `uv run` instead of direct `python3` |
| Outdated plugin installed | Run `clean` to remove old versions, reinstall with `/plugin install` |
| Import errors in plugin | Ensure `uv sync` has been run and dependencies are in `pyproject.toml` |
| Version not updating | Run `uv run scripts/update_version.py` (not manual edits) |

---

## References

- **Main README**: [README.md](README.md) - Full project documentation and plugin guide
- **Plugin Development**: [docs/plugin-development.md](docs/plugin-development.md)
- **API Reference**: [docs/api-reference.md](docs/api-reference.md)
- **Best Practices**: [docs/best-practices.md](docs/best-practices.md)
- **Supported Languages**: [docs/supported-languages.md](docs/supported-languages.md)
- **Compiled Languages Guide**: [docs/compiled-languages-guide.md](docs/compiled-languages-guide.md)
- **Local Skills**: [.claude/skills/](.claude/skills/) - Plugin & Python script organization standards
- **GitHub**: https://github.com/lazygophers/ccplugin
