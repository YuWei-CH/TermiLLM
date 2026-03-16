from __future__ import annotations

from pathlib import Path

from termillm.files import read_file
from termillm.tools.base import ToolResult


class ReadFileTool:
    name = "read_file"
    description = "Read a UTF-8 text or code file and return its contents wrapped for the model."
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
        },
        "required": ["path"],
    }

    def run(self, path: str) -> ToolResult:
        file_content, error = read_file(path)
        if error:
            return ToolResult(content=error, is_error=True)
        return ToolResult(content=file_content.llm_content)


class WriteFileTool:
    name = "write_file"
    description = "Write text content to a file path, creating parent directories if needed."
    schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }

    def run(self, path: str, content: str) -> ToolResult:
        try:
            target = Path(path).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(content=f"Wrote file: {target}")
        except Exception as exc:  # pragma: no cover - defensive filesystem path
            return ToolResult(content=f"Error writing file: {exc}", is_error=True)
