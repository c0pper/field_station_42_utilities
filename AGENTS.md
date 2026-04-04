# AGENTS.md - Field Station 42 Utilities

This is a Python project for processing and organizing video advertisements. It uses AI agents (via atomic-agents) to classify, name, and organize ads.

## Project Overview

- **Language**: Python >= 3.14
- **Package Manager**: uv
- **Key Dependencies**: atomic-agents, pydantic, instructor, openai

## Build/Lint/Test Commands

### Package Management (uv)
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Run a script with dependencies
uv run python <script.py>
```

### Running Scripts
```bash
# Run any script directly with uv
uv run python main.py <args>

# Or activate the virtual environment first
source .venv/bin/activate
python main.py <args>
```

### Running Individual Tests
This project does not have formal tests (no pytest/unittest configured). For testing individual functions:
```bash
# Test a specific function by importing it
uv run python -c "from module import function; function()"

# Run script-specific __main__ blocks for ad-hoc testing
uv run python ads_namer_agent.py
uv run python ads_show_classifier_agent.py
uv run python ads_period_classifier_agent.py
```

### Code Quality
No formal linter (ruff, flake8, etc.) or type checker (mypy) is configured. When adding them, consider:
```bash
# Linting
uv add ruff --dev
uv run ruff check .

# Type checking
uv add mypy --dev
uv run mypy .
```

## Code Style Guidelines

### Imports
- Standard library imports first
- Third-party imports second (alphabetically within groups)
- Local/relative imports last
- Use absolute imports from the project root
- Example:
  ```python
  from pathlib import Path
  import re
  
  import instructor
  from openai import OpenAI
  from pydantic import Field
  
  from ads_namer_agent import agent as namer_agent, AdsNamingOutputSchema
  from shared import VIDEO_EXTS
  ```

### Formatting
- 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (Black default)
- Use trailing commas in multi-line structures
- One blank line between top-level definitions

### Type Hints
- Use type hints for all function parameters and return types
- Use `Optional[X]` instead of `X | None` for compatibility
- Example:
  ```python
  def find_video_by_basename(folder: Path, base_name: str) -> Optional[Path]:
  ```

### Naming Conventions
- **Modules/Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Type aliases**: `PascalCase`
- **Agent classes**: End with `Agent` (e.g., `AdsNamingAgent`)
- **Schema classes**: End with `Schema` or `InputSchema`/`OutputSchema`
- **Enum members**: `UPPER_SNAKE_CASE` or `PascalCase` for string enums

### Error Handling
- Use `check=True` with `subprocess.run()` to raise on non-zero exit
- Validate paths early: `if not path.exists(): raise ValueError(...)`
- Print skip messages for expected missing files: `[SKIP] message`
- Use `missing_ok=True` for optional cleanup: `file.unlink(missing_ok=True)`

### Docstrings
- Use triple double quotes `"""`
- First line: brief description (imperative mood or third-person singular)
- Additional lines: expanded explanation if needed
- Example:
  ```python
  def unique_path(path: Path) -> Path:
      """If path exists, append _1, _2, ... before extension"""
  ```

### Logging Format
- Use bracketed prefixes for status messages:
  - `[SKIP]` - Skipped due to existing file or missing data
  - `[MERGE]` - Merging operation
  - `[COPY]` - Copying operation
  - `[AUDIO]` - Audio extraction
  - `[WHISPER]` - Transcription
  - `[RENAME]` - File renaming
  - `[MOVE]` - File movement

### File Operations
- Always use `pathlib.Path` for file paths (not os.path or strings)
- Use `resolve()` to get absolute paths from CLI args
- Use `mkdir(exist_ok=True)` for creating directories
- Handle encoding explicitly: `path.read_text(encoding="utf-8")`

### Agent Pattern
For AI agents using atomic-agents:
1. Create a `client` using `instructor.from_openai()` with local endpoint
2. Define `SystemPromptGenerator` with `background`, `steps`, `output_instructions`
3. Create input/output schemas extending `BaseIOSchema` with Pydantic `Field`
4. Create agent class extending `AtomicAgent[InputSchema, OutputSchema]`
5. Export an `agent` instance for use by other modules
6. Use `__main__` block for standalone testing

### Project Structure
```
├── *.py              # Top-level scripts and agents
├── models/           # Downloaded ML models (Whisper)
├── shared.py         # Shared utilities
└── pyproject.toml    # Project configuration
```

### CLI Conventions
- Use `argparse.ArgumentParser`
- Positional arguments for required inputs
- `--flag` style for optional flags
- Provide help text for all arguments
- Use `nargs="?"` with `default` for optional positional args
