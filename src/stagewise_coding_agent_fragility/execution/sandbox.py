"""Sandbox boundary for executing subprocess commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time


@dataclass(frozen=True)
class SandboxCommandResult:
    """Represents the result of one sandbox command execution.

    Attributes:
        stdout: Captured standard output.
        stderr: Captured standard error.
        returncode: Subprocess return code, or `None` on timeout.
        timeout: Whether the command timed out.
        runtime_seconds: Wall-clock execution time in seconds.
    """

    stdout: str
    stderr: str
    returncode: int | None
    timeout: bool
    runtime_seconds: float


class SandboxExecutor:
    """Protocol-like base class for command execution."""

    def run_command(
        self,
        command: list[str],
        working_directory: Path,
        timeout_seconds: float,
    ) -> SandboxCommandResult:
        """Run one command inside the sandbox.

        Args:
            command: Command and arguments to execute.
            working_directory: Directory in which to run the command.
            timeout_seconds: Timeout in seconds.

        Returns:
            A sandbox command result.
        """
        raise NotImplementedError


class LocalSandboxExecutor(SandboxExecutor):
    """Executes commands on the local machine with subprocess."""

    def run_command(
        self,
        command: list[str],
        working_directory: Path,
        timeout_seconds: float,
    ) -> SandboxCommandResult:
        """Run one command locally.

        Args:
            command: Command and arguments to execute.
            working_directory: Directory in which to run the command.
            timeout_seconds: Timeout in seconds.

        Returns:
            A sandbox command result.
        """
        started_at = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            runtime_seconds = time.perf_counter() - started_at
            stdout = error.stdout or ""
            stderr = error.stderr or ""
            return SandboxCommandResult(
                stdout=stdout,
                stderr=stderr,
                returncode=None,
                timeout=True,
                runtime_seconds=runtime_seconds,
            )

        runtime_seconds = time.perf_counter() - started_at
        return SandboxCommandResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            timeout=False,
            runtime_seconds=runtime_seconds,
        )
