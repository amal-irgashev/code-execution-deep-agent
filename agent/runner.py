#!/usr/bin/env python3
"""Main runner script for the Code Execution Deep Agent.

This script creates and runs the agent with:
- LocalExecutionBackend for file I/O and command execution
- SkillsMiddleware for progressive skill disclosure
- Human-in-the-Loop approval for sensitive operations
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend

from agent.backend_local_exec import LocalExecutionBackend
from agent.middleware_skills import SkillsMiddleware


def create_agent():
    """Create and configure the code execution agent.

    Returns:
        Configured agent graph ready for invocation.
    """
    # Load environment variables
    load_dotenv()

    # Validate API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in your .env file or environment variables")
        sys.exit(1)

    # Get absolute paths
    project_root = Path(__file__).parent.parent.resolve()
    workspace_dir = project_root / "workspace"
    skills_dir = project_root / "skills"

    # Ensure directories exist
    workspace_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Create backends
    # Default: LocalExecutionBackend for workspace (read-write + execute)
    workspace_backend = LocalExecutionBackend(
        root_dir=workspace_dir,
        default_timeout=120,  # 2 minutes
        max_output_chars=50_000,  # 50k chars max
    )

    # Skills: Read-only FilesystemBackend mounted at /skills/
    skills_backend = FilesystemBackend(
        root_dir=skills_dir,
        virtual_mode=True,  # Virtual paths like /skills/csv-analytics/...
    )

    # Composite backend: workspace as default, skills at /skills/
    backend = CompositeBackend(
        default=workspace_backend,
        routes={"/skills/": skills_backend},
    )

    # Create LLM
    model = ChatAnthropic(
        model_name="claude-sonnet-4-5-20250929",
        max_tokens=8000,
    )

    # Create Skills middleware
    skills_middleware = SkillsMiddleware(skills_dir=skills_dir)

    # System prompt
    system_prompt = """You are a helpful AI assistant with access to a local workspace and specialized skills.

## Your Capabilities

1. **File Operations**: You can read, write, and edit files in the workspace using `ls`, `read_file`, `write_file`, and `edit_file` tools.

2. **Command Execution**: You can run shell commands and Python scripts using the `execute` tool. This allows you to process data, run analyses, and automate tasks.

3. **Skills**: You have access to specialized skills for complex tasks. Each skill provides scripts and documentation for specific domains (CSV analysis, PDF processing, etc.).

## Important Guidelines

### Progressive Disclosure
- Don't load all skill documentation at startup
- When a user request matches a skill, use `read_file` to load only that skill's SKILL.md
- Follow the instructions in SKILL.md to use scripts effectively

### Efficient Data Processing
- For large datasets (>1000 rows), use scripts to filter/process data before summarizing
- Don't load entire large files into context - use tools to extract what you need
- Execute commands to do heavy lifting, then summarize results

### Safety
- Some operations (execute, edit_file) require user approval
- Explain what you're about to do before requesting approval
- If a command is rejected, suggest alternatives

### Workspace Organization
- Your working directory is: /workspace/
- Skills are available at: /skills/
- Data files are typically in: /workspace/data/

## Workflow Example

User: "Find the top 5 highest value orders in orders.csv"

1. Check file: `ls /workspace/data/`
2. Load skill: `read_file /skills/csv-analytics/SKILL.md`
3. Run script: `execute "python3 /skills/csv-analytics/scripts/filter_high_value.py /workspace/data/orders.csv amount 0 --top 5"`
4. Parse JSON output and present summary to user

Remember: Use skills to delegate heavy processing, keep context focused on the task at hand.
"""

    # Create agent with HITL approval for sensitive operations
    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        backend=backend,
        middleware=[skills_middleware],
        interrupt_on={
            "execute": {
                "allowed_decisions": ["approve", "reject"],
            },
            "edit_file": {
                "allowed_decisions": ["approve", "reject"],
            },
        },
    )

    return agent


def interactive_loop(agent):
    """Run an interactive loop for the agent.

    Args:
        agent: Configured agent graph.
    """
    print("\n" + "=" * 60)
    print("Code Execution Deep Agent")
    print("=" * 60)
    print("\nType 'quit' or 'exit' to end the session")
    print("Type 'help' for usage information")
    print("\nWorking directory: /workspace/")
    print("Skills available: /skills/")
    print("=" * 60 + "\n")

    config = {"configurable": {"thread_id": "main"}}

    while True:
        try:
            # Get user input
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "help":
                print("\nAvailable Commands:")
                print("  - Ask questions about your data")
                print("  - Request CSV analysis or PDF extraction")
                print("  - Execute Python scripts")
                print("  - quit/exit - End session")
                print("\nExample queries:")
                print("  'What are the top 5 orders by amount?'")
                print("  'Extract form fields from sample_form.pdf'")
                continue

            # Invoke agent
            print("\nAgent is thinking...\n")

            # Stream responses
            for chunk in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages",
            ):
                # Handle different message types
                for message in chunk:
                    if hasattr(message, "content") and message.content:
                        # Print AI responses
                        if hasattr(message, "type") and message.type == "ai":
                            print(message.content)

                    # Handle tool calls (show what's being executed)
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            print(f"\n[Tool: {tool_name}]")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            continue
        except Exception as e:
            print(f"\nError: {e}")
            import traceback

            traceback.print_exc()
            continue


def main():
    """Main entry point."""
    print("Initializing agent...")

    try:
        agent = create_agent()
        interactive_loop(agent)
    except Exception as e:
        print(f"Error initializing agent: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

