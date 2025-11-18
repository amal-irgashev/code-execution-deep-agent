"""Local execution backend that extends FilesystemBackend with command execution.

This module provides LocalExecutionBackend, which inherits from FilesystemBackend
to get secure file I/O operations and implements SandboxBackendProtocol to add
local command execution capabilities.
"""

import os
import subprocess
from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import ExecuteResponse, SandboxBackendProtocol


class LocalExecutionBackend(FilesystemBackend, SandboxBackendProtocol):
    """Backend that provides both file operations and local command execution.

    This backend inherits file operation methods (read, write, edit, ls_info, etc.)
    from FilesystemBackend and adds the execute() method to run shell commands
    locally with proper safety constraints.

    Attributes:
        default_timeout: Maximum seconds allowed for command execution (default: 120).
        max_output_chars: Maximum characters in combined output before truncation (default: 50000).
        env_allowlist: Dictionary of environment variables allowed in execution context.
    """

    def __init__(
        self,
        root_dir: str | Path | None = None,
        default_timeout: int = 120,
        max_output_chars: int = 50_000,
        env_allowlist: dict[str, str] | None = None,
    ) -> None:
        """Initialize the LocalExecutionBackend.

        Args:
            root_dir: Root directory for file operations and command execution.
                     Commands will run with cwd=root_dir.
            default_timeout: Maximum execution time in seconds (default: 120).
            max_output_chars: Maximum output size before truncation (default: 50000).
            env_allowlist: Mapping of allowed environment variables to pass to subprocesses.
                          If None, only a minimal baseline environment is used.
        """
        super().__init__(root_dir=root_dir)
        self.default_timeout = default_timeout
        self.max_output_chars = max_output_chars
        self.env_allowlist = env_allowlist or {}

    def execute(self, command: str) -> ExecuteResponse:
        """Execute a shell command in the backend's working directory.

        The command runs with:
        - cwd set to self.cwd (the backend's root directory)
        - A minimal environment (only variables in env_allowlist)
        - Configured timeout to prevent hanging
        - Output capture of both stdout and stderr

        Args:
            command: Shell command string to execute.

        Returns:
            ExecuteResponse with:
                - output: Combined stdout and stderr (possibly truncated)
                - exit_code: Process exit code (124 indicates timeout)
                - truncated: True if output was truncated
        """
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=self.default_timeout,
                env=self._build_env(),
            )

            # Combine stdout and stderr
            output = proc.stdout or ""
            if proc.stderr:
                output += ("\n" if output else "") + proc.stderr

            # Truncate if too long (preserve beginning and end)
            truncated = len(output) > self.max_output_chars
            if truncated:
                half = self.max_output_chars // 2
                head = output[:half]
                tail = output[-half:]
                output = head + "\n... [truncated] ...\n" + tail

            return ExecuteResponse(
                output=output,
                exit_code=proc.returncode,
                truncated=truncated,
            )

        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output=f"Command timed out after {self.default_timeout}s",
                exit_code=124,  # Standard timeout exit code
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(
                output=f"Error executing command: {e}",
                exit_code=1,
                truncated=False,
            )

    def _build_env(self) -> dict[str, str]:
        """Build the environment dictionary for subprocess execution.

        Only includes environment variables that are explicitly allowed via
        the env_allowlist. This provides a minimal, controlled execution
        environment for safety.

        Returns:
            Dictionary of environment variables to pass to subprocess.
        """
        env = {}
        for key in self.env_allowlist:
            if key in os.environ:
                env[key] = os.environ[key]
        
        # Always include PATH if not already in allowlist
        if "PATH" not in env and "PATH" in os.environ:
            env["PATH"] = os.environ["PATH"]
        
        return env

    @property
    def id(self) -> str:
        """Return a stable identifier for this backend instance.

        Returns:
            String identifier in format "local-exec-<directory_name>".
        """
        return f"local-exec-{self.cwd.name}"

