from __future__ import annotations

from rich import print
from rich.markdown import Markdown

from termillm.config import AppConfig
from termillm.files import read_file
from termillm.model_client import ChatModelClient
from termillm.runtime.subprocess_executor import SubprocessCommandExecutor
from termillm.tools.base import ToolRegistry
from termillm.tools.commands import RunCommandTool
from termillm.tools.filesystem import ReadFileTool, WriteFileTool


HELP_MARKDOWN = """
### Commands:
- `/model <model>`: Change the model (e.g., /model deepseek-ai/deepseek-llm-7b-chat)
- `/temp <temperature>`: Change the temperature (e.g., /temp 0.5)
- `/max_tokens <number>`: Change the maximum tokens (e.g., /max_tokens 4096)
- `/file <path>`: Read a file and add it to the conversation
- `/clear`: Clear the chat history
- `/settings`: View current settings
- `/exit`: Exit the application

### Supported File Types:
- C++ (.cpp, .cc, .h, .hpp, .cxx)
- Python (.py)
- CUDA (.cu, .cuh)
- HIP (.hip)
- Text (.txt)
- Markdown (.md)
"""


class AgentSession:
    def __init__(self, config: AppConfig, client: ChatModelClient) -> None:
        self.config = config
        self.client = client
        self.messages: list[dict[str, str]] = []
        self.tools = ToolRegistry()
        executor = SubprocessCommandExecutor()
        self.tools.register("run_command", RunCommandTool(executor))
        self.tools.register("read_file", ReadFileTool())
        self.tools.register("write_file", WriteFileTool())

    def handle_input(self, user_input: str) -> bool:
        if user_input.startswith("/"):
            return self._handle_command(user_input)

        self.messages.append({"role": "user", "content": user_input})
        response_text = self.client.stream_chat(self.config, self.messages)
        if response_text:
            self.messages.append({"role": "assistant", "content": response_text})
        return False

    def _handle_command(self, user_input: str) -> bool:
        parts = user_input.strip().split(maxsplit=1)
        command = parts[0]

        if command == "/exit":
            print("[bold red]Exiting...[/bold red]")
            return True
        if command == "/help":
            print(Markdown(HELP_MARKDOWN))
            return False
        if command == "/clear":
            self.messages.clear()
            print("[green]Conversation history cleared.[/green]")
            return False
        if command == "/file":
            return self._handle_file_command(parts)
        if command == "/model":
            return self._handle_model_command(user_input)
        if command == "/temp":
            return self._handle_temp_command(user_input)
        if command == "/max_tokens":
            return self._handle_max_tokens_command(user_input)
        if command == "/settings":
            self._print_settings()
            return False

        print(f"[yellow]Unknown command: {command}[/yellow]")
        return False

    def _handle_file_command(self, parts: list[str]) -> bool:
        if len(parts) < 2 or not parts[1].strip():
            print("[yellow]Please provide a file path.[/yellow]")
            print("[dim]Usage: /file /path/to/file.py[/dim]")
            return False

        file_path = parts[1].strip()
        print(f"[dim]Reading file: {file_path}...[/dim]")
        file_content, error = read_file(file_path)
        if error:
            print(f"[bold red]{error}[/bold red]")
            return False

        print(f"[green]{file_content.info}[/green]")
        print(file_content.renderable())
        file_message = (
            f"I'm sharing the contents of file {file_content.path.name}:\n\n"
            f"{file_content.llm_content}"
        )
        self.messages.append({"role": "user", "content": file_message})
        print("[green]File content added to the conversation. You can now ask questions about it.[/green]")
        return False

    def _handle_model_command(self, user_input: str) -> bool:
        if user_input.strip() == "/model":
            print(f"[cyan]Current model:[/cyan] {self.config.model}")
            return False

        if not user_input.startswith("/model "):
            print("[red]Usage: /model <model_name>[/red]")
            return False

        new_model = user_input[len("/model ") :].strip()
        if not new_model:
            print("[red]Usage: /model <model_name>[/red]")
            return False

        previous_model = self.config.model
        self.config.model = new_model
        print(f"[dim]Checking availability of model '{new_model}'...[/dim]")
        if self.client.check_model_availability(self.config):
            self.config.save()
            print(f"[cyan]Model set to:[/cyan] {self.config.model}")
            print("[dim]Model preference saved for future sessions.[/dim]")
            return False

        self.config.model = previous_model
        print(f"[red]Could not set model to '{new_model}'. Keeping current model: {previous_model}[/red]")
        return False

    def _handle_temp_command(self, user_input: str) -> bool:
        if user_input.strip() == "/temp":
            print(f"[cyan]Current temperature:[/cyan] {self.config.temperature}")
            return False

        if not user_input.startswith("/temp "):
            print("[red]Usage: /temp <float_value> (e.g., /temp 0.8)[/red]")
            return False

        try:
            new_temp = float(user_input[len("/temp ") :].strip())
        except ValueError:
            print("[red]Usage: /temp <float_value> (e.g., /temp 0.8)[/red]")
            return False

        if not 0 <= new_temp <= 2:
            print("[red]Temperature should be between 0 and 2.[/red]")
            return False

        self.config.temperature = new_temp
        self.config.save()
        print(f"[cyan]Temperature set to:[/cyan] {self.config.temperature}")
        print("[dim]Temperature preference saved for future sessions.[/dim]")
        return False

    def _handle_max_tokens_command(self, user_input: str) -> bool:
        if user_input.strip() == "/max_tokens":
            print(f"[cyan]Current max_tokens:[/cyan] {self.config.max_tokens}")
            return False

        if not user_input.startswith("/max_tokens "):
            print("[red]Usage: /max_tokens <int_value> (e.g., /max_tokens 4096)[/red]")
            return False

        try:
            new_max_tokens = int(user_input[len("/max_tokens ") :].strip())
        except ValueError:
            print("[red]Usage: /max_tokens <int_value> (e.g., /max_tokens 4096)[/red]")
            return False

        if new_max_tokens <= 0:
            print("[red]Max tokens should be a positive integer.[/red]")
            return False

        self.config.max_tokens = new_max_tokens
        self.config.save()
        print(f"[cyan]Max tokens set to:[/cyan] {self.config.max_tokens}")
        print("[dim]Max tokens preference saved for future sessions.[/dim]")
        return False

    def _print_settings(self) -> None:
        print(
            Markdown(
                f"""
### Current Settings:
- **Model**: {self.config.model}
- **Server URL**: {self.config.base_url}
- **Temperature**: {self.config.temperature}
- **Max Tokens**: {self.config.max_tokens}
"""
            )
        )

