from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

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
- `/mode [chat|auto|agent]`: Change or view the interaction mode
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


@dataclass
class AgentDecision:
    action: str
    content: str = ""
    tool_name: str = ""
    args: dict | None = None


class AgentSession:
    def __init__(self, config: AppConfig, client: ChatModelClient) -> None:
        self.config = config
        self.client = client
        self.mode = "chat"
        self.messages: list[dict[str, str]] = []
        self.tools = ToolRegistry()
        executor = SubprocessCommandExecutor()
        self.tools.register(RunCommandTool(executor))
        self.tools.register(ReadFileTool())
        self.tools.register(WriteFileTool())

    def handle_input(self, user_input: str) -> bool:
        if user_input.startswith("/"):
            return self._handle_command(user_input)

        self.messages.append({"role": "user", "content": user_input})
        if self.mode == "chat":
            response_text = self.client.stream_chat(self.config, self.messages)
            if response_text:
                self.messages.append({"role": "assistant", "content": response_text})
            return False

        response_text = self._run_agent_loop()
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
        if command == "/mode":
            return self._handle_mode_command(user_input)
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

    def _handle_mode_command(self, user_input: str) -> bool:
        if user_input.strip() == "/mode":
            print(f"[cyan]Current mode:[/cyan] {self.mode}")
            return False

        if not user_input.startswith("/mode "):
            print("[red]Usage: /mode <chat|auto|agent>[/red]")
            return False

        new_mode = user_input[len("/mode ") :].strip().lower()
        if new_mode not in {"chat", "auto", "agent"}:
            print("[red]Usage: /mode <chat|auto|agent>[/red]")
            return False

        self.mode = new_mode
        print(f"[cyan]Mode set to:[/cyan] {self.mode}")
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
- **Mode**: {self.mode}
- **Model**: {self.config.model}
- **Server URL**: {self.config.base_url}
- **Temperature**: {self.config.temperature}
- **Max Tokens**: {self.config.max_tokens}
"""
            )
        )

    def _run_agent_loop(self, max_steps: int = 5) -> str:
        working_messages = self._build_agent_messages()
        for _ in range(max_steps):
            assistant_text = self.client.complete(self.config, working_messages)
            if not assistant_text:
                return ""

            decision = self._parse_agent_response(assistant_text)
            if decision.action == "final":
                print("[bold magenta]Assistant:[/bold magenta] ", end="")
                print(decision.content)
                return decision.content

            if decision.action == "tool":
                tool_result = self._execute_tool(decision.tool_name, decision.args or {})
                print(f"[dim]Tool {decision.tool_name} result:[/dim]")
                print(tool_result.content)
                working_messages.append({"role": "assistant", "content": assistant_text})
                working_messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Tool result for `{decision.tool_name}`:\n"
                            f"{tool_result.content}\n"
                            "Continue and either call another tool or provide the final answer "
                            "using the required JSON response format."
                        ),
                    }
                )
                continue

            if decision.action == "retry":
                working_messages.append({"role": "assistant", "content": assistant_text})
                working_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not follow the required JSON protocol. "
                            "Reply with exactly one JSON object. "
                            "If you need local information, call an appropriate tool."
                        ),
                    }
                )
                continue

            print("[bold magenta]Assistant:[/bold magenta] ", end="")
            print(assistant_text)
            return assistant_text

        timeout_message = "Agent stopped after reaching the maximum tool steps."
        print(f"[yellow]{timeout_message}[/yellow]")
        return timeout_message

    def _build_agent_messages(self) -> list[dict[str, str]]:
        messages = [
            {
                "role": "system",
                "content": self._agent_system_prompt(),
            }
        ]
        tool_hint = self._latest_tool_hint()
        if tool_hint:
            messages.append({"role": "system", "content": tool_hint})
        messages.extend(self.messages)
        return messages

    def _agent_system_prompt(self) -> str:
        mode_guidance = {
            "auto": "Use tools only when they are necessary to answer correctly.",
            "agent": "Prefer tools whenever they would improve confidence or gather facts.",
        }.get(self.mode, "Answer normally.")
        tool_lines = "\n".join(
            f"- {item['name']}: {item['description']} | schema: {json.dumps(item['schema'], ensure_ascii=True)}"
            for item in self.tools.definitions()
        )
        return (
            "You are TermiLLM operating as a terminal assistant.\n"
            f"{mode_guidance}\n"
            "If the user asks about the local machine, current directory, files, or project contents, "
            "do not answer from memory. Use tools to inspect the environment first.\n"
            "Available tools:\n"
            f"{tool_lines}\n\n"
            "You must respond with exactly one JSON object and no extra text.\n"
            'For a tool call use: {"action":"tool","tool":"tool_name","args":{...}}\n'
            'For the final answer use: {"action":"final","content":"..."}'
        )

    def _parse_agent_response(self, assistant_text: str) -> AgentDecision:
        payload = assistant_text.strip()
        if payload.startswith("```json") and payload.endswith("```"):
            payload = payload[len("```json") : -3].strip()
        elif payload.startswith("```") and payload.endswith("```"):
            payload = payload[3:-3].strip()

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            if self.mode in {"auto", "agent"}:
                return AgentDecision(action="retry", content=assistant_text)
            return AgentDecision(action="text", content=assistant_text)

        action = parsed.get("action")
        if action == "tool":
            return AgentDecision(
                action="tool",
                tool_name=parsed.get("tool", ""),
                args=parsed.get("args") or {},
            )
        if action == "final":
            return AgentDecision(action="final", content=parsed.get("content", ""))
        if self.mode in {"auto", "agent"}:
            return AgentDecision(action="retry", content=assistant_text)
        return AgentDecision(action="text", content=assistant_text)

    def _execute_tool(self, tool_name: str, args: dict) -> object:
        try:
            tool = self.tools.get(tool_name)
        except KeyError:
            return type("ToolError", (), {"content": f"Unknown tool: {tool_name}"})()

        try:
            return tool.run(**args)
        except TypeError as exc:
            return type("ToolError", (), {"content": f"Invalid arguments for {tool_name}: {exc}"})()

    def _latest_tool_hint(self) -> str:
        latest_user_message = next(
            (message["content"] for message in reversed(self.messages) if message["role"] == "user"),
            "",
        )
        lowered = latest_user_message.lower()
        cwd = Path.cwd()

        if self._looks_like_directory_question(lowered):
            return (
                "Tool hint: the user is asking about the current folder or directory contents. "
                "Call `run_command` with `pwd` and/or `ls -la`. "
                f"The current working directory for this session is `{cwd}`."
            )

        file_match = re.search(
            r"(?:read|open|show|inspect|summarize|explain)\s+(?:the\s+)?file\s+([^\s]+)",
            latest_user_message,
            re.IGNORECASE,
        )
        if file_match:
            return (
                "Tool hint: the user appears to be asking about a specific file. "
                f"Prefer `read_file` for `{file_match.group(1)}` before answering."
            )

        if any(keyword in lowered for keyword in {"run ", "execute ", "command ", "shell "}):
            return (
                "Tool hint: the user likely expects actual command execution. "
                "Prefer `run_command` over a purely descriptive answer."
            )

        return ""

    def _looks_like_directory_question(self, lowered: str) -> bool:
        patterns = (
            "this folder",
            "current folder",
            "this directory",
            "current directory",
            "in this repo",
            "in this project",
            "what files",
            "list files",
            "what is in",
            "what's in",
            "what do i have",
            "contents of this",
        )
        return any(pattern in lowered for pattern in patterns)
