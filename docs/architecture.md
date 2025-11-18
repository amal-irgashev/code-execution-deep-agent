# Technical Architecture & Requirements: Local Code-Execution Agent

This document outlines the technical requirements, architectural design, and implementation strategy for building a **Local Code-Executing Deep Agent**. The goal is to build an agent with a "full computer" context (storage + execution) that uses **Progressive Disclosure** to manage complex skills without context bloat.

## 1. Project Overview

We are building a supervisor agent that runs locally on the user's machine. It does **not** use Docker or MCP. Instead, it relies on standard Python libraries and the `deepagents` framework to execute code safely on the host OS while managing capabilities via a file-based "Skills" system.

### Core Objectives
1.  **Local Execution**: Implement a backend that allows the agent to run shell commands on the host.
2.  **Progressive Disclosure**: Inject high-level skill metadata into the system prompt, allowing the agent to "pull" detailed instructions (`SKILL.md`) and tools (`scripts/`) only when needed.
3.  **Educational Architecture**: Demonstrate clear separation between **Middleware** (Prompt/Tool injection), **Backends** (I/O & Execution), and **Agent Graph** (Logic).

---

## 2. Leveraged Library: `deepagents`

We are building on top of the `deepagents` library. We will leverage its specific abstractions to avoid reinventing the wheel.

### Existing Components to Use
*   **`FilesystemMiddleware`**: We will *not* rewrite this. We will use the existing middleware which provides `ls`, `read_file`, `write_file`, etc. Crucially, `FilesystemMiddleware` automatically detects if a backend implements `SandboxBackendProtocol` and injects the `execute` tool if it does.
*   **`FilesystemBackend`**: Provides secure file I/O (handling `O_NOFOLLOW`, path normalization, etc.). Our custom backend will inherit from this to inherit these safety features.
*   **`CompositeBackend`**: Allows us to mount our "Skills" directory as read-only at a virtual path (e.g., `/skills/`) while keeping the workspace read-write.
*   **`create_deep_agent`**: The main factory for wiring the LangGraph nodes, middleware, and LLM together.
*   **`BackendProtocol` & `SandboxBackendProtocol`**: The interfaces we must implement to make our custom execution backend compatible with the middleware.

---

## 3. New Components to Implement

### A. `LocalExecutionBackend`
**Role**: The interface between the Agent and the OS. It handles both File I/O and Command Execution.

**Inheritance**:
```python
class LocalExecutionBackend(FilesystemBackend, SandboxBackendProtocol):
```
*   Inherits from `FilesystemBackend` to get `read`, `write`, `ls_info` implementation for free.
*   Implements `SandboxBackendProtocol` to provide the `execute` method.

**Requirements**:
1.  **`execute(command: str) -> ExecuteResponse`**:
    *   Uses `subprocess.run` with `shell=True`.
    *   **Context**: MUST run in `self.cwd`.
    *   **Output**: Combines `stdout` and `stderr`.
    *   **Safety**: Implements strict timeouts (exit code 124 on timeout) and output truncation (max chars) to prevent context context overflow.
2.  **`id` property**: Returns a stable identifier for the backend instance.

### B. `SkillsMiddleware`
**Role**: Implements the **Progressive Disclosure** pattern.

**Inheritance**:
```python
class SkillsMiddleware(AgentMiddleware):
```

**Requirements**:
1.  **Initialization**: Accepts a path to the `skills/` directory.
2.  **`before_agent`**:
    *   Scans `skills/*/SKILL.md`.
    *   Parses YAML Frontmatter (Name, Description).
    *   Stores this metadata in `AgentState`.
3.  **`wrap_model_call`**:
    *   Injects a section into the System Prompt listing available skills.
    *   *Crucial*: Does NOT inject the full skill content. It instructs the agent to use `read_file` to load the specific `SKILL.md` if the description matches the user's request.

---

## 4. Data Structures & Protocols

### Skills Repository Structure
The agent does not have tools hardcoded in Python. Instead, capabilities are defined in files:
```text
skills/
├── pdf-processing/
│   ├── SKILL.md               # Frontmatter + Usage Instructions
│   ├── scripts/               # Executable Python scripts
│   │   └── extract_forms.py
│   └── docs/                  # Supporting documentation
│       └── forms.md
```

**The Workflow**:
1.  **Discovery**: Middleware sees `pdf-processing`.
2.  **Prompting**: LLM sees "pdf-processing: Extract text/tables..." in system prompt.
3.  **Activation**: LLM calls `read_file("/skills/pdf-processing/SKILL.md")`.
4.  **Execution**: LLM reads instructions, sees it needs to run a script, and calls `execute("python3 /skills/pdf-processing/scripts/extract_forms.py ...")`.

### Backend Protocol Adherence
Our `LocalExecutionBackend` must satisfy `deepagents.backends.protocol.SandboxBackendProtocol`:

```python
@runtime_checkable
class SandboxBackendProtocol(BackendProtocol, Protocol):
    def execute(self, command: str) -> ExecuteResponse: ...
    @property
    def id(self) -> str: ...
```

---

## 5. Safety & Configuration

Since we are allowing local execution, we must configure the agent with Human-in-the-Loop (HITL) safety rails using `deepagents` configuration patterns.

**`interrupt_on` Configuration**:
We will configure the `create_deep_agent` call to require approval for high-risk tools:
```python
interrupt_on={
    "execute": {"allowed_decisions": ["approve", "reject"]},
    "edit_file": {"allowed_decisions": ["approve", "reject"]},
    # "write_file" - optional
}
```

---

## 6. Development Roadmap

1.  **Week 1: The Backend**
    *   Implement `LocalExecutionBackend`.
    *   Unit tests ensuring `execute` handles timeouts, cwd, and output capture correctly.
2.  **Week 2: The Middleware**
    *   Implement `SkillsMiddleware`.
    *   Implement metadata scanning and prompt injection.
    *   Create the `csv-analytics` and `pdf-processing` example skills.
3.  **Week 3: Integration & Demo**
    *   Wire it all together using `create_deep_agent`.
    *   Mount the backend using `CompositeBackend` (Workspace RW / Skills RO).
    *   Verify the full "Prompt -> Read Skill -> Execute Script" loop.

## 7. Why This Architecture?

*   **vs. Docker**: Docker requires heavy setup and privileges. This approach runs where the user is, making it strictly a "user agent" acting with the user's permissions.
*   **vs. MCP**: MCP abstracts tools behind a server. Here, we want the agent to "own" the tools as files, allowing it to read, understand, and even *edit* its own scripts if permitted (self-evolution).
*   **Progressive Disclosure**: Prevents the context window from filling up with tool definitions for 50 skills when only 1 is needed.

