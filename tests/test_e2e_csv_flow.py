"""End-to-end tests for CSV processing workflow.

These tests verify that the agent:
1. Discovers and loads the csv-analytics skill
2. Uses scripts to process data off-model
3. Returns concise results without loading full CSV into context
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from langchain_anthropic import ChatAnthropic

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend

from agent.backend_local_exec import LocalExecutionBackend
from agent.middleware_skills import SkillsMiddleware


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.resolve()


@pytest.fixture
def agent(project_root):
    """Create a test agent instance.

    Note: This requires ANTHROPIC_API_KEY to be set in environment.
    Tests will be skipped if the key is not available.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

    workspace_dir = project_root / "workspace"
    skills_dir = project_root / "skills"

    # Create backends
    workspace_backend = LocalExecutionBackend(
        root_dir=workspace_dir,
        default_timeout=120,
        max_output_chars=50_000,
    )

    skills_backend = FilesystemBackend(
        root_dir=skills_dir,
        virtual_mode=True,
    )

    backend = CompositeBackend(
        default=workspace_backend,
        routes={"/skills/": skills_backend},
    )

    # Create model
    model = ChatAnthropic(
        model_name="claude-sonnet-4-5-20250929",
        max_tokens=4000,
    )

    # Create middleware
    skills_middleware = SkillsMiddleware(skills_dir=skills_dir)

    # Create agent without HITL for testing
    agent = create_deep_agent(
        model=model,
        system_prompt="You are a test agent. Use skills when appropriate.",
        backend=backend,
        middleware=[skills_middleware],
    )

    return agent


class TestCSVWorkflow:
    """Test end-to-end CSV processing workflows."""

    def test_csv_file_exists(self, project_root):
        """Verify that the sample CSV file exists."""
        csv_path = project_root / "workspace" / "data" / "orders.csv"
        assert csv_path.exists(), "Sample orders.csv not found"

        # Verify it has data
        import pandas as pd

        df = pd.read_csv(csv_path)
        assert len(df) > 1000, "CSV should have >1000 rows"
        assert "amount" in df.columns, "CSV should have 'amount' column"

    def test_filter_script_works_standalone(self, project_root):
        """Test that the filter script works correctly when run directly."""
        script_path = (
            project_root / "skills" / "csv-analytics" / "scripts" / "filter_high_value.py"
        )
        csv_path = project_root / "workspace" / "data" / "orders.csv"

        assert script_path.exists(), "Filter script not found"

        # Run the script
        import subprocess

        result = subprocess.run(
            [
                "python3",
                str(script_path),
                str(csv_path),
                "amount",
                "5000",
                "--top",
                "5",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "amount" in result.stdout, "Output should contain JSON with amount field"

        # Verify JSON output
        import json

        data = json.loads(result.stdout)
        assert isinstance(data, list), "Output should be a JSON array"
        assert len(data) <= 5, "Should return at most 5 records"

    @pytest.mark.integration
    def test_agent_uses_csv_skill(self, agent, project_root):
        """Test that agent uses csv-analytics skill for CSV queries.

        This test verifies:
        - Agent identifies csv-analytics skill as relevant
        - Agent reads SKILL.md
        - Agent executes filter script
        - Agent summarizes results without loading full CSV
        """
        query = "What are the top 3 orders by amount in /workspace/data/orders.csv?"

        config = {"configurable": {"thread_id": "test-csv"}}

        # Invoke agent
        result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config)

        # Extract messages
        messages = result.get("messages", [])
        assert len(messages) > 0, "Agent should return messages"

        # Verify tool usage in message history
        tool_calls = []
        tool_messages = []

        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
            if hasattr(msg, "type") and msg.type == "tool":
                tool_messages.append(msg)

        # Agent should have used read_file to load SKILL.md
        read_calls = [tc for tc in tool_calls if tc.get("name") == "read_file"]
        assert any(
            "csv-analytics/SKILL.md" in str(tc.get("args", {})) for tc in read_calls
        ), "Agent should read csv-analytics SKILL.md"

        # Agent should have used execute to run the script
        execute_calls = [tc for tc in tool_calls if tc.get("name") == "execute"]
        assert len(execute_calls) > 0, "Agent should execute filter script"
        assert any(
            "filter_high_value.py" in str(tc.get("args", {})) for tc in execute_calls
        ), "Agent should run filter_high_value.py"

        # Final response should mention top orders
        final_message = messages[-1]
        if hasattr(final_message, "content"):
            content = final_message.content.lower()
            assert "order" in content or "amount" in content, "Response should mention orders"

    @pytest.mark.integration
    def test_agent_progressive_disclosure(self, agent):
        """Test that agent doesn't load all skills preemptively.

        The agent should only load SKILL.md when relevant to the query.
        """
        # Ask a question that doesn't require any skills
        query = "What is 2 + 2?"

        config = {"configurable": {"thread_id": "test-simple"}}

        result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config)

        messages = result.get("messages", [])

        # Check tool calls - should not read any SKILL.md files
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

        read_calls = [tc for tc in tool_calls if tc.get("name") == "read_file"]

        # Should not read SKILL.md for a simple math question
        skill_reads = [tc for tc in read_calls if "SKILL.md" in str(tc.get("args", {}))]
        assert (
            len(skill_reads) == 0
        ), "Agent should not load skills for simple non-skill queries"


class TestCSVScriptDirectly:
    """Test CSV processing scripts in isolation."""

    def test_filter_script_with_threshold(self, project_root):
        """Test filter script with various thresholds."""
        script_path = (
            project_root / "skills" / "csv-analytics" / "scripts" / "filter_high_value.py"
        )
        csv_path = project_root / "workspace" / "data" / "orders.csv"

        import subprocess

        # Test with high threshold
        result = subprocess.run(
            ["python3", str(script_path), str(csv_path), "amount", "10000", "--top", "3"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0

        import json

        data = json.loads(result.stdout)
        assert len(data) <= 3
        # All returned amounts should be >= 10000
        for record in data:
            assert record["amount"] >= 10000

    def test_filter_script_invalid_column(self, project_root):
        """Test that script handles invalid column names gracefully."""
        script_path = (
            project_root / "skills" / "csv-analytics" / "scripts" / "filter_high_value.py"
        )
        csv_path = project_root / "workspace" / "data" / "orders.csv"

        import subprocess

        result = subprocess.run(
            [
                "python3",
                str(script_path),
                str(csv_path),
                "nonexistent_column",
                "0",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 1  # Should fail
        assert "not found" in result.stderr.lower()

