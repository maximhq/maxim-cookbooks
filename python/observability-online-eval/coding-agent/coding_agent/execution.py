"""
Subprocess execution environment for running generated code.

Adapted from gpt-engineer's DiskExecutionEnv, simplified for cookbook clarity.
"""

import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from coding_agent.files import FilesDict


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    return_code: int


class ExecutionEnvironment:
    """Manages a temp directory for writing and executing generated code."""

    def __init__(self, workdir: str = None):
        self.workdir = workdir or tempfile.mkdtemp(prefix="coding_agent_")

    def write_files(self, files: FilesDict):
        """Write files to disk, creating subdirectories as needed."""
        workdir_path = Path(self.workdir).resolve()
        for filename, content in files.items():
            filepath = (workdir_path / filename).resolve()
            try:
                filepath.relative_to(workdir_path)
            except ValueError as exc:
                raise ValueError(f"Invalid path outside workdir: {filename}") from exc
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open("w") as f:
                f.write(content)

    def execute(self, command: str = "bash run.sh", timeout: int = 30) -> ExecutionResult:
        """Run command via subprocess, capture stdout/stderr."""
        try:
            result = subprocess.run(
                shlex.split(command),
                cwd=self.workdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timed out after {timeout}s",
                return_code=-1,
            )

    def cleanup(self):
        """Remove temp directory."""
        if os.path.exists(self.workdir):
            shutil.rmtree(self.workdir, ignore_errors=True)
