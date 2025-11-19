"""Configuration for the Code Execution Deep Agent.

All configurables including paths, timeouts, model settings, and backend creation.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from deepagents.backends import CompositeBackend, FilesystemBackend

from libs.backends import DockerExecutionBackend
from libs.middleware import SkillsMiddleware
from agent.prompt import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Get API key (validation happens when agent is used)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
SKILLS_DIR = PROJECT_ROOT / "skills"

# Ensure directories exist
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
for subdir in ("data", "scripts", "results", "competitors", "reports"):
    (WORKSPACE_DIR / subdir).mkdir(parents=True, exist_ok=True)
# Ensure nested directories for competitive intelligence
(WORKSPACE_DIR / "reports" / "daily").mkdir(parents=True, exist_ok=True)

# Execution settings
DEFAULT_TIMEOUT = 120  # seconds
MAX_OUTPUT_CHARS = 50_000  # characters
CONTAINER_NAME = "code-execution-agent"  # Docker container name

# Model settings
MODEL_NAME = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 8000

# Create backends
workspace_backend = DockerExecutionBackend(
    root_dir=WORKSPACE_DIR,
    container_name=CONTAINER_NAME,
    default_timeout=DEFAULT_TIMEOUT,
    max_output_chars=MAX_OUTPUT_CHARS,
)

skills_backend = FilesystemBackend(
    root_dir=SKILLS_DIR,
    virtual_mode=True,
)

backend = CompositeBackend(
    default=workspace_backend,
    routes={
        "/skills/": skills_backend,
    },
)

# Create model
model = ChatAnthropic(
    model_name=MODEL_NAME,
    max_tokens=MAX_TOKENS,
)

# Discover skills at import time (eager loading for efficiency)
# This runs synchronously during module import, before any async event loop exists
_skills_discovery = SkillsMiddleware(skills_dir=SKILLS_DIR)
DISCOVERED_SKILLS = _skills_discovery.skills

# Create middleware with pre-discovered skills
skills_middleware = SkillsMiddleware(
    skills_dir=SKILLS_DIR,
    discovered_skills=DISCOVERED_SKILLS,
)

# HITL configuration
INTERRUPT_ON = {
    "execute": {
        "allowed_decisions": ["approve", "reject"],
    },
    "edit_file": {
        "allowed_decisions": ["approve", "reject"],
    },
}

# ==============================================================================
# Competitive Intelligence Subagent Configuration
# ==============================================================================
# This subagent researches a single competitor using specialized web search skills.
# It operates in isolated context to keep main agent's context clean.
#
# Workflow:
# 1. Main agent delegates per-competitor research via task() tool
# 2. Subagent discovers and uses web search skills (news, blogs, docs)
# 3. Subagent writes aggregated findings to /competitors/{slug}/research/{date}.json
# 4. Returns concise summary to main agent for aggregation
# ==============================================================================

# Subagent model configuration
# Format: Can be either:
#   - Claude model name: "claude-sonnet-4-5-20250929" (uses ChatAnthropic)
SUBAGENT_MODEL = "gpt-5-mini"

competitive_research_subagent = {
    "name": "competitor-researcher",
    "description": (
        "Research a single competitor by gathering recent news, announcements, "
        "blog posts, and documentation updates. Use this subagent when you need "
        "to investigate what a specific competitor has been doing recently."
    ),
    "model": SUBAGENT_MODEL,
    "system_prompt": """You are a competitive intelligence researcher focused on ONE competitor.

**Mission**: Gather comprehensive intelligence using web search skills (news, blogs, docs), then return a concise executive summary.

**Key Principles**:
- **Token efficiency**: Use `--output` flags to write search results to files, not your context
- **Focused scope**: Research only your assigned competitor, stay in `/competitors/{slug}/`
- **Structured output**: Save aggregated findings to `/competitors/{slug}/research/{today}.json`
- **Executive summary**: Return 3-5 bullet points highlighting strategic implications

**Available Skills**:
- `web-search-news` - Recent press releases (7 days)
- `web-search-blogs` - Technical articles (30 days)  
- `web-search-docs` - Documentation updates (14 days)

Read skill SKILL.md files for detailed usage instructions when needed.

**Your Deliverable**:
1. Search results saved to files (news.json, blogs.json, docs.json)
2. Aggregated research summary saved to `research/{today}.json`
3. Executive summary returned to main agent (3-5 strategic bullets)

Stay focused on your assigned competitor. Delegate research to skills, synthesize strategic insights.""",
    "tools": [],  # Tools come from middleware (filesystem + execute)
    "middleware": [
        # Subagent uses the same SkillsMiddleware as main agent
        # This gives it access to web-search-news, web-search-blogs, web-search-docs
        SkillsMiddleware(
            skills_dir=SKILLS_DIR,
            discovered_skills=DISCOVERED_SKILLS,  # Reuse discovered skills
        ),
        # FilesystemMiddleware is automatically attached by create_deep_agent
    ],
}

# Export subagents list for graph.py
SUBAGENTS = [competitive_research_subagent]
