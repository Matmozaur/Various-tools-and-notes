"""
Basic UV commands demonstration
"""

def show_basic_commands():
    """Show basic uv commands"""
    
    print("UV Package Manager - Basic Commands")
    print("=" * 35)
    
    commands = [
        ("uv init", "Create new project"),
        ("uv add requests", "Add dependency"),
        ("uv remove requests", "Remove dependency"),
        ("uv sync", "Install dependencies"),
        ("uv run python script.py", "Run Python script"),
        ("uv pip list", "List installed packages"),
    ]
    
    for cmd, desc in commands:
        print(f"{cmd:<25} # {desc}")

if __name__ == "__main__":
    show_basic_commands()
