"""Docker-based sandbox boundary for executing subprocess commands."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from stagewise_coding_agent_fragility.execution.sandbox import SandboxCommandResult, SandboxExecutor


class DockerSandboxExecutor(SandboxExecutor):
    """Executes commands inside an ephemeral Docker container."""

    def __init__(self, image_name: str) -> None:
        """Initialize the Docker sandbox.

        Args:
            image_name: The Docker image to use for the container. Must be
                available locally or pullable.
        """
        self._image_name = image_name

    def run_command(
        self,
        command: list[str],
        working_directory: Path,
        timeout_seconds: float,
    ) -> SandboxCommandResult:
        """Run one command inside a Docker container.

        Mounts the given working directory into the container at the exact same
        absolute path, sets the working directory, and executes the command.

        Args:
            command: Command and arguments to execute.
            working_directory: Directory in which to run the command.
            timeout_seconds: Timeout in seconds.

        Returns:
            A sandbox command result.
        """
        # Ensure working directory is absolute to avoid mount ambiguities.
        abs_workspace = working_directory.absolute()

        docker_command = [
            "docker",
            "run",
            "--rm",
            "--network=none",  # Isolate network by default for security
            "-v",
            f"{abs_workspace}:{abs_workspace}",
            "-w",
            str(abs_workspace),
            self._image_name,
        ] + command

        started_at = time.perf_counter()
        try:
            completed = subprocess.run(
                docker_command,
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
