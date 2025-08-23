# UV Package Manager - Basic Example

UV is a fast Python package installer and resolver written in Rust.

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init my-project
cd my-project

# Add dependencies
uv add requests

# Run code
uv run python main.py
```

## Key Benefits
- 10-100x faster than pip
- Automatic lockfile generation
- Built-in project management
