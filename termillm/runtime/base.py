from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class CommandExecutionRequest:
    command: list[str]
    cwd: Path | None = None
    timeout_sec: int = 20
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class CommandExecutionResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class CommandExecutor(Protocol):
    def run(self, request: CommandExecutionRequest) -> CommandExecutionResult:
        ...

