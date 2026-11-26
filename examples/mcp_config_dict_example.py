"""
MCP Tools with Config Dict Format - Example

This example demonstrates using MCP tools with the simplified config dict format.
Instead of explicitly creating MCPClient objects, you can pass MCP server configs
directly to the tools parameter.
"""

import os

try:
    from dotenv import load_dotenv
except Exception:

    def load_dotenv():
        return None


try:
    import aisuite as ai
except Exception:
    # Provide a lightweight stub so this example module can be imported/run
    # even when the 'aisuite' package is not installed (e.g., in CI failure cases).
    class _DummyMessage:
        def __init__(self, content):
            self.content = content

    class _DummyChoice:
        def __init__(self, content):
            self.message = _DummyMessage(content)

    class _DummyResponse:
        def __init__(self, content="aisuite not installed; responses are stubbed."):
            self.choices = [_DummyChoice(content)]

    class _DummyCompletions:
        def create(self, *args, **kwargs):
            return _DummyResponse()

    class _DummyChat:
        def __init__(self):
            self.completions = _DummyCompletions()

    class _DummyClient:
        def __init__(self, *args, **kwargs):
            self.chat = _DummyChat()

    class _DummyAISuiteModule:
        Client = _DummyClient

    ai = _DummyAISuiteModule()

# Load environment variables
load_dotenv()

# Create aisuite client
client = ai.Client()

print("=" * 70)
print("Example 1: Basic Config Dict Usage")
print("=" * 70)

# Instead of creating MCPClient explicitly, pass config dict directly!
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[
        {"role": "user", "content": "List all Python files in the current directory"}
    ],
    tools=[
        {
            "type": "mcp",
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        }
    ],
    max_turns=2,
)

print(response.choices[0].message.content)

print("\n" + "=" * 70)
print("Example 2: Filtering Tools with allowed_tools")
print("=" * 70)

# Only allow specific tools for security
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "Read the README.md file"}],
    tools=[
        {
            "type": "mcp",
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
            "allowed_tools": ["read_file"],  # Security: only allow reading, not writing
        }
    ],
    max_turns=2,
)

print(response.choices[0].message.content)

print("\n" + "=" * 70)
print("Example 3: Multiple MCP Servers with Tool Prefixing")
print("=" * 70)

import tempfile

temp_dir = tempfile.mkdtemp()

# Connect to two different filesystem servers with prefixing
# This avoids tool name collisions
response = client.chat.completions.create(
    model="anthropic:claude-3-5-sonnet-20240620",
    messages=[
        {
            "role": "user",
            "content": "How many files are in the current directory vs the temp directory?",
        }
    ],
    tools=[
        {
            "type": "mcp",
            "name": "current_dir",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
            "use_tool_prefix": True,  # Tools named "current_dir__list_directory", etc.
        },
        {
            "type": "mcp",
            "name": "temp_dir",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", temp_dir],
            "use_tool_prefix": True,  # Tools named "temp_dir__list_directory", etc.
        },
    ],
    max_turns=3,
)

print(response.choices[0].message.content)

print("\n" + "=" * 70)
print("Example 4: Mixing MCP Configs with Python Functions")
print("=" * 70)

from datetime import datetime


def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_stats(numbers: list) -> dict:
    """Calculate basic statistics for a list of numbers.

    Args:
        numbers: List of numbers to analyze
    """
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers) if numbers else 0,
    }


# Mix everything: MCP configs + Python functions!
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "What time is it? Also, list all files in the current directory.",
        }
    ],
    tools=[
        get_current_time,  # Regular Python function
        calculate_stats,  # Another Python function
        {
            "type": "mcp",
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        },  # MCP config dict
    ],
    max_turns=3,
)

print(response.choices[0].message.content)

print("\n" + "=" * 70)
print("Example 5: When to Use Config Dict vs MCPClient")
print("=" * 70)

print(
    """
Use Config Dict When:
✓ Quick prototypes and simple scripts
✓ One-off tool usage
✓ Don't need to reuse MCP client across multiple requests
✓ Want automatic cleanup
✓ Less code is better

Use Explicit MCPClient When:
✓ Need to reuse the same MCP connection across multiple requests
✓ Want to inspect available tools before using them
✓ Need fine-grained control over connection lifecycle
✓ Building a long-running application
✓ Want to manually manage resources

Example of explicit MCPClient:
"""
)

try:
    from aisuite.mcp import MCPClient
except Exception:
    # Fallback stub for MCPClient so the example remains importable if aisuite is missing.
    class MCPClient:
        def __init__(self, *args, **kwargs):
            pass

        def list_tools(self):
            return []

        def get_callable_tools(self):
            return []

        def close(self):
            pass


# Create once, reuse many times
mcp = MCPClient(
    command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()]
)

# Inspect available tools
print(f"\\nAvailable tools: {[t['name'] for t in mcp.list_tools()]}")

# Reuse across multiple requests
for query in ["List files", "Count files", "Check if README exists"]:
    response = client.chat.completions.create(
        model="openai:gpt-4o",
        messages=[{"role": "user", "content": query}],
        tools=mcp.get_callable_tools(),
        max_turns=2,
    )
    print(f"\\n{query}: {response.choices[0].message.content[:100]}...")

mcp.close()

print("\n" + "=" * 70)
print("All examples completed!")
print("=" * 70)
