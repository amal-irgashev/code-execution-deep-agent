"""End-to-end tests for PDF processing workflow.

These tests verify that the agent:
1. Discovers and loads the pdf-processing skill
2. Uses scripts to extract form data
3. Returns structured results
"""

import os
from pathlib import Path

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


class TestPDFWorkflow:
    """Test end-to-end PDF processing workflows."""

    def test_pdf_file_exists(self, project_root):
        """Verify that the sample PDF file exists."""
        pdf_path = project_root / "workspace" / "data" / "sample_form.pdf"
        assert pdf_path.exists(), "Sample sample_form.pdf not found"

        # Verify it has form fields
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        fields = reader.get_form_text_fields()
        assert fields is not None, "PDF should have form fields"
        assert len(fields) > 0, "PDF should have at least one form field"

    def test_extract_script_works_standalone(self, project_root):
        """Test that the extract_forms script works correctly when run directly."""
        script_path = (
            project_root / "skills" / "pdf-processing" / "scripts" / "extract_forms.py"
        )
        pdf_path = project_root / "workspace" / "data" / "sample_form.pdf"

        assert script_path.exists(), "Extract script not found"

        # Run the script
        import subprocess

        result = subprocess.run(
            ["python3", str(script_path), str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Verify JSON output
        import json

        data = json.loads(result.stdout)
        assert "fields" in data, "Output should have 'fields' key"
        assert "metadata" in data, "Output should have 'metadata' key"
        assert len(data["fields"]) > 0, "Should extract at least one field"

    @pytest.mark.integration
    def test_agent_uses_pdf_skill(self, agent, project_root):
        """Test that agent uses pdf-processing skill for PDF queries.

        This test verifies:
        - Agent identifies pdf-processing skill as relevant
        - Agent reads SKILL.md
        - Agent executes extract_forms script
        - Agent returns extracted form data
        """
        query = "Extract the form fields from /workspace/data/sample_form.pdf"

        config = {"configurable": {"thread_id": "test-pdf"}}

        # Invoke agent
        result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config)

        # Extract messages
        messages = result.get("messages", [])
        assert len(messages) > 0, "Agent should return messages"

        # Verify tool usage
        tool_calls = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

        # Agent should have used read_file to load SKILL.md
        read_calls = [tc for tc in tool_calls if tc.get("name") == "read_file"]
        assert any(
            "pdf-processing/SKILL.md" in str(tc.get("args", {})) for tc in read_calls
        ), "Agent should read pdf-processing SKILL.md"

        # Agent should have used execute to run the script
        execute_calls = [tc for tc in tool_calls if tc.get("name") == "execute"]
        assert len(execute_calls) > 0, "Agent should execute extract_forms script"
        assert any(
            "extract_forms.py" in str(tc.get("args", {})) for tc in execute_calls
        ), "Agent should run extract_forms.py"

        # Final response should mention extracted fields
        final_message = messages[-1]
        if hasattr(final_message, "content"):
            content = final_message.content.lower()
            assert (
                "field" in content or "form" in content or "name" in content
            ), "Response should mention form fields"

    @pytest.mark.integration
    def test_agent_handles_nonexistent_pdf(self, agent):
        """Test that agent handles requests for non-existent PDFs gracefully."""
        query = "Extract form fields from /workspace/data/nonexistent.pdf"

        config = {"configurable": {"thread_id": "test-missing-pdf"}}

        # Invoke agent
        result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config)

        messages = result.get("messages", [])
        final_message = messages[-1]

        # Agent should report that file doesn't exist
        if hasattr(final_message, "content"):
            content = final_message.content.lower()
            assert (
                "not found" in content or "does not exist" in content or "error" in content
            ), "Agent should report file not found"


class TestPDFScriptDirectly:
    """Test PDF processing scripts in isolation."""

    def test_extract_forms_with_valid_pdf(self, project_root):
        """Test extract_forms.py with valid PDF."""
        script_path = (
            project_root / "skills" / "pdf-processing" / "scripts" / "extract_forms.py"
        )
        pdf_path = project_root / "workspace" / "data" / "sample_form.pdf"

        import subprocess

        result = subprocess.run(
            ["python3", str(script_path), str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0

        import json

        data = json.loads(result.stdout)
        assert "fields" in data
        assert "metadata" in data
        assert data["metadata"]["total_fields"] > 0

        # Check that we got the expected fields
        fields = data["fields"]
        assert "Name" in fields
        assert "Email" in fields

    def test_extract_forms_with_missing_file(self, project_root):
        """Test that script handles missing files gracefully."""
        script_path = (
            project_root / "skills" / "pdf-processing" / "scripts" / "extract_forms.py"
        )

        import subprocess

        result = subprocess.run(
            ["python3", str(script_path), "/nonexistent/file.pdf"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 1  # Should fail
        assert "not found" in result.stderr.lower()

