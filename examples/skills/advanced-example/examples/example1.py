"""
Advanced example demonstrating complex skill usage.

This example shows how to structure more sophisticated code examples
that demonstrate the skill's capabilities.
"""

from typing import Any


class SkillExample:
    """Example class demonstrating skill concepts."""

    def __init__(self, name: str, complexity: str = "intermediate") -> None:
        """
        Initialize the example.

        Args:
            name: Example name
            complexity: Complexity level
        """
        self.name = name
        self.complexity = complexity
        self.metadata: dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the example.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_info(self) -> dict[str, Any]:
        """
        Get example information.

        Returns:
            Dictionary with example info
        """
        return {
            "name": self.name,
            "complexity": self.complexity,
            "metadata": self.metadata,
        }


def main() -> None:
    """Main function demonstrating the example."""
    # Create an example instance
    example = SkillExample("advanced-demo", "advanced")

    # Add some metadata
    example.add_metadata("version", "2.0.1")
    example.add_metadata("author", "MCP Skills Team")
    example.add_metadata("tags", ["example", "advanced"])

    # Display information
    info = example.get_info()
    print("Example Information:")
    print(f"  Name: {info['name']}")
    print(f"  Complexity: {info['complexity']}")
    print(f"  Metadata: {info['metadata']}")

    print("\n✓ This example demonstrates:")
    print("  - Object-oriented design")
    print("  - Type hints")
    print("  - Docstrings")
    print("  - Metadata management")


if __name__ == "__main__":
    main()
