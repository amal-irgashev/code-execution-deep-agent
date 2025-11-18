#!/usr/bin/env python3
"""Verification script to check that all components are properly set up."""

from pathlib import Path

from agent.middleware_skills import SkillsMiddleware
from agent.backend_local_exec import LocalExecutionBackend


def main():
    """Verify the setup."""
    print("=" * 60)
    print("Code Execution Deep Agent - Setup Verification")
    print("=" * 60)
    print()

    project_root = Path(__file__).parent
    
    # Check skills
    print("1. Checking Skills Discovery...")
    skills_dir = project_root / "skills"
    middleware = SkillsMiddleware(skills_dir=skills_dir)
    skills = middleware._discover_skills()
    
    print(f"   Found {len(skills)} skills:")
    for skill in skills:
        print(f"   - {skill['name']}: {skill['description']}")
    print()

    # Check backend
    print("2. Checking LocalExecutionBackend...")
    workspace_dir = project_root / "workspace"
    backend = LocalExecutionBackend(root_dir=workspace_dir)
    print(f"   Backend ID: {backend.id}")
    print(f"   Working directory: {backend.cwd}")
    
    # Test execution
    result = backend.execute("echo 'Hello from backend'")
    print(f"   Test execution: exit_code={result.exit_code}, output='{result.output.strip()}'")
    print()

    # Check sample data
    print("3. Checking Sample Data...")
    csv_path = workspace_dir / "data" / "orders.csv"
    pdf_path = workspace_dir / "data" / "sample_form.pdf"
    
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        print(f"   ✓ orders.csv exists ({len(df):,} rows)")
    else:
        print(f"   ✗ orders.csv not found")
    
    if pdf_path.exists():
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        fields = reader.get_form_text_fields()
        print(f"   ✓ sample_form.pdf exists ({len(fields or {})} form fields)")
    else:
        print(f"   ✗ sample_form.pdf not found")
    print()

    # Check scripts are executable
    print("4. Checking Scripts...")
    csv_script = project_root / "skills" / "csv-analytics" / "scripts" / "filter_high_value.py"
    pdf_script = project_root / "skills" / "pdf-processing" / "scripts" / "extract_forms.py"
    
    if csv_script.exists():
        print(f"   ✓ filter_high_value.py exists")
    else:
        print(f"   ✗ filter_high_value.py not found")
    
    if pdf_script.exists():
        print(f"   ✓ extract_forms.py exists")
    else:
        print(f"   ✗ extract_forms.py not found")
    print()

    print("=" * 60)
    print("✓ Setup verification complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Set ANTHROPIC_API_KEY in .env file")
    print("2. Run: uv run python agent/runner.py")
    print()


if __name__ == "__main__":
    main()

