from __future__ import annotations

import shlex
from pathlib import Path

from termillm.runtime.base import CommandExecutionRequest, CommandExecutor
from termillm.tools.base import ToolResult


class RunCommandTool:
    name = "run_command"
    description = "Run a non-interactive terminal command and return stdout, stderr, and exit code."
    schema = {
        "type": "object",
        "properties": {
            "command": {
                "oneOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"},
                ]
            },
            "cwd": {"type": ["string", "null"]},
            "timeout_sec": {"type": "integer", "minimum": 1},
        },
        "required": ["command"],
    }

    def __init__(self, executor: CommandExecutor) -> None:
        self.executor = executor

    def run(self, command: list[str] | str, cwd: str | None = None, timeout_sec: int = 20) -> ToolResult:
        if isinstance(command, str):
            command = shlex.split(command)

        result = self.executor.run(
            CommandExecutionRequest(
                command=command,
                cwd=Path(cwd).expanduser() if cwd else None,
                timeout_sec=timeout_sec,
            )
        )
        content = (
            f"exit_code: {result.exit_code}\n"
            f"timed_out: {result.timed_out}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        return ToolResult(content=content, is_error=result.exit_code != 0 or result.timed_out)
