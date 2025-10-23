"""
Demo Python script for the intermediate-example skill.

This file demonstrates how to include example files in a skill folder.
"""


def greet(name: str) -> str:
    """
    Simple greeting function.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}! Welcome to the MCP Skills Server."


def main() -> None:
    """Main function."""
    print(greet("Claude"))
    print("\nThis is an example file referenced in the SKILL.md frontmatter.")
    print("Example files can be any format: .py, .txt, .md, .json, etc.")


if __name__ == "__main__":
    main()
