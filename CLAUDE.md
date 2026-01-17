# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CCPlugin Market** is a Claude Code plugin marketplace that provides high-quality plugins and development templates for the Claude Code ecosystem. The project includes:

- **Code Plugins** (`plugins/code/`): 13 language and framework plugins (Python, Go, TypeScript, JavaScript, React, Vue, Next.js, Ant Design, Flutter, and tools like semantic search, Git, version management)
- **Style Plugins** (`plugins/style/`): 12 UI design style plugins (Glassmorphism, Neumorphism, Gradient, Neon, Retro, Brutalism, Minimal, Dark, Pastel, Vibrant, HighContrast, Luxe)
- **Utility Plugins** (`plugins/`): Task management and notification system
- **Shared Library**: `lib/` directory with reusable code components extracted from all plugins
- **Entry Points**: Command-line scripts in `plugins/*/scripts/` that use the shared library

## Architecture

### High-Level Structure

```
ccplugin/
├── lib/                          # Shared library (reorganized in recent refactoring)
│   ├── config/                   # Configuration management (paths, YAML loading)
│   ├── constants/                # Language definitions (SUPPORTED_LANGUAGES)
│   ├── embedding/                # Vector embedding generation (FastEmbed, CodeModel)
│   ├── parsers/                  # Multi-language code parsing (Python, Go, JS, etc.)
│   ├── database/                 # Code indexing and storage (LanceDB integration)
│   ├── search/                   # Query processing and semantic search
│   ├── utils/                    # Helper utilities and hybrid indexer
│   ├── mcp/                      # MCP protocol integration
│   └── tests/                    # Comprehensive test suite
│
├── plugins/
│   ├── code/                     # Language and framework development plugins
│   │   ├── python/               # Python development standards
│   │   ├── golang/               # Go development standards
│   │   ├── javascript/           # JavaScript (ES2024+) standards
│   │   ├── typescript/           # TypeScript development standards
│   │   ├── react/                # React 18+ development standards
│   │   ├── vue/                  # Vue 3 development standards
│   │   ├── nextjs/               # Next.js 16+ full-stack development
│   │   ├── antd/                 # Ant Design 5.x enterprise UI
│   │   ├── flutter/              # Flutter mobile development
│   │   ├── semantic/             # Semantic code search (uses lib/*)
│   │   ├── git/                  # Git version control operations
│   │   ├── version/              # Version number management
│   │   ├── template/             # Plugin development template
│   │   ├── README.md             # Code plugins overview and guide
│   │   └── [plugin-name]/        # Individual plugin structure
│   │       ├── skills/
│   │       ├── scripts/
│   │       ├── agents/
│   │       └── commands/
│   │
│   ├── style/                    # UI design style plugins
│   │   ├── style-glassmorphism/  # Glass morphism design style
│   │   ├── style-neumorphism/    # Neumorphism design style
│   │   ├── style-gradient/       # Gradient art style
│   │   ├── style-neon/           # Neon cyberpunk style
│   │   ├── style-retro/          # Retro vintage style
│   │   ├── style-brutalism/      # Brutalism design style
│   │   ├── style-minimal/        # Minimalist style
│   │   ├── style-dark/           # Dark mode style
│   │   ├── style-pastel/         # Soft pastel style
│   │   ├── style-vibrant/        # Vibrant high-contrast style
│   │   ├── style-highcontrast/   # High contrast accessibility style
│   │   ├── style-luxe/           # Luxe premium style
│   │   ├── README.md             # Style plugins overview and guide
│   │   └── [style-name]/         # Individual style plugin structure
│   │       └── skills/
│   │
│   ├── task/                     # Task management plugin
│   │   ├── scripts/
│   │   └── ...
│   │
│   └── notify/                   # Notification system plugin
│       ├── scripts/
│       └── ...
│
├── .claude/                      # Claude Code configuration
│   ├── skills/                   # Reusable skills for plugin development
│   │   └── plugin-skills-authoring.md  # Plugin skill authoring guidelines
│   ├── agents/                   # Specialized sub-agents
│   ├── commands/                 # Custom slash commands
│   └── settings.json
│
└── pyproject.toml                # Project metadata and build configuration
```

### Key Architecture Decisions

**1. Shared Library (lib/ directory)**
- Extracted from three main plugins (semantic, task, template)
- Contains 40+ Python modules organized by functional domain
- Used by plugin scripts to avoid code duplication
- Absolute imports required (`from lib.module import ...`)

**2. Import System**
- Plugins use `sys.path` manipulation to find the lib/ directory
- All files are proper Python packages with `__init__.py`
- Uses setuptools with explicit package discovery (`include = ["lib*", "plugins*"]`)

**3. Plugin Scripts**
- Entry points defined in `pyproject.toml` under `[project.scripts]`
- Scripts handle `sys.path` setup before importing lib modules
- Can be executed via `uv run` or as installed commands

**4. Multi-language Code Parsing**
- Factory function `parse_file()` in `lib/parsers/__init__.py`
- Language-specific parsers (PythonParser, GoParser, etc.)
- Fallback to SimpleParser for unknown languages

**5. Plugin Directory Organization**
- **plugins/code/** - 13 language and framework development plugins
  - Includes: Python, Go, TypeScript, JavaScript, React, Vue, Next.js, Ant Design, Flutter
  - Tools: Semantic search, Git, version management, development template
  - Each plugin has its own skills, scripts, agents, and commands
- **plugins/style/** - 12 UI design style plugins following 2025 design trends
  - Covers: Glassmorphism, Neumorphism, Gradient, Neon, Retro, Brutalism, Minimal, Dark, Pastel, Vibrant, HighContrast, Luxe
  - All style plugins use multi-file skills structure (SKILL.md, reference.md, examples.md)
- **plugins/** - Utility plugins (task, notify) and directory documentation
  - Task: Task management and organization
  - Notify: System notification and hook event handling

**6. Plugin Skills Structure (Anthropic Best Practices)**
- All plugins use progressive disclosure pattern with multi-file skills:
  - **SKILL.md** (300-400 lines): Navigation hub with core features and quick start
  - **reference.md**: Detailed configuration, API reference, and specifications
  - **examples.md**: Implementation examples, best practices, and FAQ
  - Optional domain-specific files for complex plugins (e.g., design-system.md, performance.md)
- YAML frontmatter with `name` and `description` fields (required)
- Third-person descriptions following Anthropic standards
- See `.claude/skills/plugin-skills-authoring.md` for complete authoring guidelines

## Development Commands

### Setup & Dependencies

```bash
# Install uv (Python package manager - mandatory)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies from pyproject.toml
uv sync

# Install a specific package
uv pip install package-name
```

### Running Code

```bash
# Execute Python scripts (mandatory - must use uv)
# Code plugins
uv run plugins/code/semantic/scripts/semantic.py --help
uv run plugins/code/semantic/scripts/semantic.py index --path lib/config
uv run plugins/code/git/scripts/git.py status
uv run plugins/code/version/scripts/version.py show

# Utility plugins
uv run plugins/task/scripts/task.py list
uv run plugins/notify/scripts/notifier.py "Title" "Message" 5000

# Run installed command-line tools
semantic init
semantic index
semantic search "function definition"

task add "New feature"
task list
task stats

# Execute tests
uv run -m pytest lib/tests/ -v
```

### Git Operations

```bash
# Check status
git status

# View recent commits
git log --oneline -10

# Make commits
git add -A
git commit -m "feat: description"
git push origin master
```

### Plugin Development

```bash
# Create new code plugin from template
cp -r plugins/code/template plugins/code/my-plugin

# Create new style plugin
cp -r plugins/style/style-template plugins/style/my-style

# Install local plugin for testing
/plugin install ./plugins/code/my-plugin

# Validate plugin structure
ls plugins/code/my-plugin/.claude-plugin/plugin.json
ls plugins/style/my-style/.claude-plugin/plugin.json
```

## Important Implementation Details

### Plugin Script Development

**All plugin scripts follow these conventions:**

1. **Help Support**
   - Scripts support `-h` and `--help` flags to display usage information
   - Example: `uv run plugins/version/scripts/version.py -h`
   - Scripts should gracefully handle missing arguments

2. **Version Management** (`plugins/version/scripts/version.py`)
   - Manages semantic versioning with 4 parts: major.minor.patch.build
   - Key methods:
     - `show`: Display current version
     - `bump [level]`: Update version (default: build)
     - `set <version>`: Manually set version
     - `init`: Initialize version file
   - Constraint: `.version` file must be committed to git before bumping versions
   - Exit with code 1 and provide hint if `.version` has uncommitted changes

3. **Hook Scripts** (`plugins/notify/scripts/*.py`)
   - Receive JSON via stdin from Claude Code
   - Validate input parameters using `validate_hook_input()` function
   
   **Stop Hook** (`stop_hook.py`):
   ```json
   {
     "session_id": "abc123",
     "transcript_path": "path/to/transcript.jsonl",
     "permission_mode": "default",
     "hook_event_name": "Stop",
     "stop_hook_active": true
   }
   ```
   
   **Notification Hook** (`notification_hook.py`):
   ```json
   {
     "session_id": "abc123",
     "message": "Permission request message",
     "notification_type": "permission_prompt|warning|info|error",
     "cwd": "/current/working/directory",
     "permission_mode": "default",
     "hook_event_name": "Notification",
     "stop_hook_active": false
   }
   ```

4. **Script Permissions**
   - All scripts in `plugins/*/scripts/` must have executable permissions (`+x`)
   - Commands in `hooks.json` should use `uv run` instead of `uvx` for hook scripts
   - Hook scripts are NOT registered as global commands in `pyproject.toml`

### lib/ Module Structure & Imports

Each lib module is a proper Python package with `__init__.py` that exports key classes/functions:

```python
# lib/config/__init__.py
from .path_manager import get_data_path, load_config

# lib/embedding/__init__.py
from .generator import EmbeddingGenerator, generate_code_id, truncate_code
from .code_model import CodeModelEngine
from .storage import LanceDBStorage

# lib/database/__init__.py
from .indexer import CodeIndexer
from .symbol_index import SymbolIndex, SymbolExtractor
```

**Plugin scripts must use absolute imports:**
```python
import sys
from pathlib import Path

# Find project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
if not (project_root / 'lib').exists():
    # Search upward up to 5 levels
    current = script_dir
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

# Now import lib modules
from lib.embedding import EmbeddingGenerator
from lib.database import CodeIndexer
from lib.parsers import parse_file
```

### Code Parsing Pipeline

The semantic plugin uses a multi-layer parsing architecture:

```
Input File → detect_language() → parse_file() → CodeParser
                                      ↓
                                   PythonParser (uses AST)
                                   GoParser (uses tree-sitter)
                                   JavaScriptParser (uses tree-sitter)
                                   SimpleParser (line-based fallback)
                                      ↓
                        List[Dict] with {type, name, code, start_line, end_line}
```

**Key Point**: `parse_file()` factory function handles initialization differences:
- `PythonParser()` - no arguments
- Other parsers - require `language` argument

### Embedding & Storage

**Vector Embeddings**:
- Primary: FastEmbed (multilingual-e5-large by default)
- Alternative: CodeModel (code-specific)
- Stored in LanceDB with vector dimension based on model

**Storage**:
- Uses LanceDB for lightweight vector storage
- Creates indices with IVF_PQ or HNSW strategies
- Data stored in `.lazygophers/ccplugin/<plugin-name>/`

### MCP Server Integration

Plugins expose MCP server endpoints for Claude Code integration:

```
plugins/code/semantic/scripts/mcp_server.py  →  semantic-mcp command
plugins/task/scripts/mcp_server.py           →  task-mcp command
```

MCP servers wrap the plugin scripts and handle protocol-specific I/O.

## Common Development Tasks

### Fixing Import Errors

If you see `ModuleNotFoundError: No module named 'lib.X'`:

1. Verify `lib/X/__init__.py` exists
2. Check that plugin script has correct `sys.path` setup
3. Ensure imports use absolute paths (`from lib.module import ...`)
4. Verify the module exports required classes in `__init__.py`

### Adding a New Language Parser

1. Create `lib/parsers/language_parser.py` with class extending `CodeParser`
2. Implement `parse_file()` and `parse_code()` methods
3. Add language mapping in `lib/parsers/__init__.py` factory function
4. Add file extensions to `lib/constants/language_constants.py`
5. Run tests: `uv run -m pytest lib/tests/test_integration.py`

### Running Code Indexing Locally

```bash
# Index a small directory first to verify
uv run plugins/code/semantic/scripts/semantic.py index --path lib/config --batch-size 10

# Index entire project (takes time for large codebases)
uv run plugins/code/semantic/scripts/semantic.py index --path . --batch-size 50
```

### Testing Plugin Scripts Locally

```bash
# Display help for any plugin script
uv run plugins/code/version/scripts/version.py -h
uv run plugins/notify/scripts/notifier.py --help

# Test version management
uv run plugins/code/version/scripts/version.py show
uv run plugins/code/version/scripts/version.py bump patch

# Test hook scripts with JSON input
echo '{"session_id":"test","hook_event_name":"Stop","transcript_path":"/tmp/test.jsonl"}' | \
  uv run plugins/notify/scripts/stop_hook.py

# Display notification
uv run plugins/notify/scripts/notifier.py "Title" "Message" 5000

# Test semantic search
uv run plugins/code/semantic/scripts/semantic.py init
uv run plugins/code/semantic/scripts/semantic.py index --path lib/config
uv run plugins/code/semantic/scripts/semantic.py search "function definition"
```

### Testing via uvx (Remote Installation)

```bash
# Clear cache and test latest commit
rm -rf ~/.cache/uv/*
cd /tmp
uvx --from git+https://github.com/lazygophers/ccplugin semantic init
uvx --from git+https://github.com/lazygophers/ccplugin semantic --help
```

## Mandatory Development Rules

### Python Execution
- **MUST use `uv run`** - Never use `python3` or `python` directly
- All plugin scripts must be executable via `uv run plugins/X/scripts/script.py`

### Code Organization
- Code plugin scripts stay in `plugins/code/*/scripts/`
- Style plugin scripts stay in `plugins/style/*/scripts/` (usually just skills)
- Utility plugin scripts stay in `plugins/{task,notify}/scripts/`
- Reusable code goes in `lib/`
- Each lib/ module must be a proper package with `__init__.py`

### Import Paths
- Plugins use **absolute imports**: `from lib.module import X`
- sys.path manipulation required in plugin entry points
- Never import from `semantic`, `task` modules directly

### Testing
- Test files in `lib/tests/`
- Run before committing: `uv run -m pytest lib/tests/ -v`
- Test coverage should increase with new lib modules

### Script Development Guidelines
- All scripts must support `-h` and `--help` flags
- Hook scripts receive JSON via stdin and must validate input parameters
- Hook scripts should exit with code 1 on validation failure
- All scripts in `plugins/code/*/scripts/`, `plugins/style/*/scripts/`, and `plugins/{task,notify}/scripts/` must have executable permissions
- Use `uv run` to execute scripts locally, never use `python3` directly
- Hook commands in `hooks.json` should use `uv run` for project-local scripts
- Skills must follow progressive disclosure pattern: SKILL.md (navigation) → reference.md (details) → examples.md (use cases)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'lib.*'` | Check `__init__.py` exports; verify `sys.path` setup in plugin script |
| `TypeError: X.__init__() takes 1 positional argument but 2 were given` | Check parser initialization - PythonParser needs no args, others need language |
| `ValueError: dimension mismatch in LanceDB` | Verify embedding model dimensions match stored vectors (usually 384 or 1024) |
| `SSL connection timeout` | Temporary network issue - retry git push/pull after waiting |
| Indexing shows 0 chunks indexed | Run `semantic init` first; verify file extensions match SUPPORTED_LANGUAGES |
| Hook script exits with code 1 | Check JSON input format and required fields; see Plugin Script Development section |
| `Failed to spawn: plugins/notify/scripts/stop_hook.py` | Verify script has executable permissions (`chmod +x`) and hooks.json uses `uv run` command |
| `.version` file cannot be bumped | Commit `.version` file to git first: `git add .version && git commit -m "initial version"` |

## References

- **README.md** - Plugin descriptions, installation, and quick start
- **lib/README.md** - Detailed API documentation for lib/ modules
- **plugins/*/README.md** - Individual plugin documentation
- **pyproject.toml** - Project metadata, dependencies, entry points
- **Official Claude Code Docs** - https://code.claude.com/docs
