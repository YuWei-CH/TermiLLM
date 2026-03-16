from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def register(self, name: str, tool: object) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> object:
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

