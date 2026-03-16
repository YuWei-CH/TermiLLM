from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.markdown import Markdown
from rich.syntax import Syntax


FILE_TYPE_MAPPING = {
    ".cpp": "c++",
    ".cc": "c++",
    ".h": "c++",
    ".hpp": "c++",
    ".cxx": "c++",
    ".py": "python",
    ".cu": "cuda",
    ".cuh": "cuda",
    ".hip": "cpp",
    ".txt": "text",
    ".md": "markdown",
}


@dataclass
class FileContent:
    path: Path
    raw: str
    language: str
    size_kb: float

    @property
    def info(self) -> str:
        return f"File: {self.path.name} ({self.size_kb:.1f} KB)"

    @property
    def llm_content(self) -> str:
        return f"```{self.language}\n{self.raw}\n```"

    def renderable(self):
        if self.path.suffix.lower() == ".md":
            return Markdown(self.raw)
        return Syntax(self.raw, self.language, theme="monokai", line_numbers=True)


def read_file(file_path: str) -> tuple[FileContent | None, str | None]:
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return None, f"File not found: {path}"

        raw = path.read_text(encoding="utf-8", errors="replace")
        suffix = path.suffix.lower()
        language = FILE_TYPE_MAPPING.get(suffix, "text")
        size_kb = path.stat().st_size / 1024
        return FileContent(path=path, raw=raw, language=language, size_kb=size_kb), None
    except Exception as exc:  # pragma: no cover - defensive UI path
        return None, f"Error reading file: {exc}"

