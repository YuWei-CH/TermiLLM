from __future__ import annotations

import os
import subprocess

from termillm.runtime.base import CommandExecutionRequest, CommandExecutionResult


class SubprocessCommandExecutor:
    def run(self, request: CommandExecutionRequest) -> CommandExecutionResult:
        env = os.environ.copy()
        env.update(request.env)

        try:
            completed = subprocess.run(
                request.command,
                cwd=request.cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=request.timeout_sec,
                check=False,
            )
            return CommandExecutionResult(
                command=request.command,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandExecutionResult(
                command=request.command,
                exit_code=-1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
            )

