"""Test runner for Python candidate code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import tempfile

from stagewise_coding_agent_fragility.execution.execution_result import ExecutionResult
from stagewise_coding_agent_fragility.execution.sandbox import LocalSandboxExecutor
from stagewise_coding_agent_fragility.execution.sandbox import SandboxExecutor
from stagewise_coding_agent_fragility.execution.sandbox import SandboxCommandResult


@dataclass(frozen=True)
class PythonTestTask:
    """Represents one Python task that can be executed with inline tests.

    Attributes:
        task_id: Stable task identifier.
        test_code: Python test code to execute after the candidate code.
    """

    task_id: str
    test_code: str


class PythonTestRunner:
    """Runs Python candidate code against inline test code."""

    def __init__(
        self,
        sandbox_executor: SandboxExecutor | None = None,
        python_executable: str | None = None,
    ) -> None:
        """Initialize the runner.

        Args:
            sandbox_executor: Sandbox executor implementation.
            python_executable: Python executable path to use for subprocess runs.
        """
        self._sandbox_executor = sandbox_executor or LocalSandboxExecutor()
        self._python_executable = python_executable or sys.executable

    def run(
        self,
        task: PythonTestTask,
        candidate_code: str,
        timeout_seconds: float,
    ) -> ExecutionResult:
        """Execute candidate code against a task's test code.

        Args:
            task: Python task definition.
            candidate_code: Candidate Python source code.
            timeout_seconds: Execution timeout in seconds.

        Returns:
            A normalized execution result.
        """
        with tempfile.TemporaryDirectory(prefix="scaf-exec-") as temporary_directory:
            working_directory = Path(temporary_directory)
            script_path = self._write_execution_script(
                working_directory=working_directory,
                candidate_code=candidate_code,
                test_code=task.test_code,
            )
            command_result = self._sandbox_executor.run_command(
                command=[self._python_executable, str(script_path)],
                working_directory=working_directory,
                timeout_seconds=timeout_seconds,
            )
        return self._build_execution_result(command_result)

    def _write_execution_script(
        self,
        working_directory: Path,
        candidate_code: str,
        test_code: str,
    ) -> Path:
        """Write the combined execution script to a temporary directory.

        Args:
            working_directory: Temporary working directory.
            candidate_code: Candidate Python source code.
            test_code: Python test code.

        Returns:
            Path to the generated script file.
        """
        script_path = working_directory / "submission.py"
        combined_script = self._build_execution_script(candidate_code, test_code)
        script_path.write_text(combined_script, encoding="utf-8")
        return script_path

    def _build_execution_script(self, candidate_code: str, test_code: str) -> str:
        """Build a single Python script from code and tests.

        Args:
            candidate_code: Candidate Python source code.
            test_code: Python test code.

        Returns:
            Combined executable Python script.
        """
        stripped_candidate_code = candidate_code.rstrip()
        stripped_test_code = test_code.rstrip()
        return f"{stripped_candidate_code}\n\n{stripped_test_code}\n"

    def _build_execution_result(
        self,
        command_result: SandboxCommandResult,
    ) -> ExecutionResult:
        """Convert a sandbox command result into an execution result.

        Args:
            command_result: Result from the sandbox layer.

        Returns:
            Normalized execution result.
        """
        if command_result.timeout:
            return ExecutionResult(
                passed=False,
                stdout=command_result.stdout,
                stderr=command_result.stderr,
                timeout=True,
                runtime_seconds=command_result.runtime_seconds,
                raw_failure="Execution timed out.",
                parsed_failure={"failure_type": "timeout"},
            )

        passed = command_result.returncode == 0
        raw_failure = self._extract_raw_failure(command_result)
        parsed_failure = None if passed else self._parse_failure(raw_failure)
        return ExecutionResult(
            passed=passed,
            stdout=command_result.stdout,
            stderr=command_result.stderr,
            timeout=False,
            runtime_seconds=command_result.runtime_seconds,
            raw_failure=raw_failure,
            parsed_failure=parsed_failure,
        )

    def _extract_raw_failure(self, command_result: SandboxCommandResult) -> str:
        """Extract raw failure text from stdout and stderr.

        Args:
            command_result: Result from the sandbox layer.

        Returns:
            Raw failure text, or an empty string on success.
        """
        if command_result.returncode == 0:
            return ""
        stderr_text = command_result.stderr.strip()
        if stderr_text:
            return stderr_text
        return command_result.stdout.strip()

    def _parse_failure(self, raw_failure: str) -> dict[str, str]:
        """Parse raw failure text into a minimal structured summary.

        Args:
            raw_failure: Raw failure text.

        Returns:
            Parsed failure metadata.
        """
        stripped_failure = raw_failure.strip()
        if not stripped_failure:
            return {"failure_type": "unknown", "message": ""}

        lines = [line.strip() for line in stripped_failure.splitlines() if line.strip()]
        final_line = lines[-1]
        exception_type = final_line.split(":", maxsplit=1)[0]
        return {
            "failure_type": "exception",
            "exception_type": exception_type,
            "message": final_line,
        }
