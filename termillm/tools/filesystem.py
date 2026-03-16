from __future__ import annotations

from pathlib import Path

from termillm.files import read_file
from termillm.tools.base import ToolResult


class ReadFileTool:
    def run(self, path: str) -> ToolResult:
        file_content, error = read_file(path)
        if error:
            return ToolResult(content=error, is_error=True)
        return ToolResult(content=file_content.llm_content)


class WriteFileTool:
    def run(self, path: str, content: str) -> ToolResult:
        try:
            target = Path(path).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(content=f"Wrote file: {target}")
        except Exception as exc:  # pragma: no cover - defensive filesystem path
            return ToolResult(content=f"Error writing file: {exc}", is_error=True)

