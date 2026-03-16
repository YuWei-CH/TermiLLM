from __future__ import annotations

import json
import re

import requests
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from termillm.config import AppConfig


class ChatModelClient:
    def check_model_availability(self, config: AppConfig) -> bool:
        try:
            models_url = f"{config.base_url}/v1/models"
            response = requests.get(models_url, timeout=5)

            if response.status_code == 200:
                models_data = response.json()
                available_models = [model_info["id"] for model_info in models_data.get("data", [])]
                if config.model in available_models:
                    return True

                print(
                    f"[bold yellow]Warning:[/bold yellow] Model '{config.model}' "
                    "not found in available models."
                )
                if available_models:
                    print(f"Available models: {', '.join(available_models)}")
                return False

            return self._test_chat_endpoint(config)
        except requests.exceptions.RequestException as exc:
            print(f"[bold red]Connection to vLLM server failed:[/bold red] {exc}")
            return False

    def _test_chat_endpoint(self, config: AppConfig) -> bool:
        chat_url = f"{config.base_url}/v1/chat/completions"
        payload = {
            "model": config.model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "stream": False,
        }

        response = requests.post(chat_url, headers={"Content-Type": "application/json"}, json=payload, timeout=10)
        if response.status_code == 200:
            return True

        error_message = f"HTTP {response.status_code}"
        try:
            error_data = response.json()
            if "error" in error_data:
                error_message = error_data["error"].get("message", error_message)
        except Exception:
            pass
        print(f"[bold red]Model check failed:[/bold red] {error_message}")
        return False

    def stream_chat(self, config: AppConfig, messages: list[dict[str, str]]) -> str:
        url = f"{config.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": True,
        }

        console = Console()
        response_text = ""
        buffer = ""
        in_code_block = False
        code_language = ""

        try:
            print("[bold magenta]Assistant:[/bold magenta] ", end="", flush=True)
            with requests.post(url, headers=headers, json=payload, stream=True) as response:
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[len("data: ") :].strip()
                    if data == "[DONE]":
                        if buffer:
                            print(buffer, end="", flush=True)
                        continue

                    try:
                        content = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    delta = content.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if not delta:
                        continue

                    buffer += delta
                    response_text += delta

                    code_block_start = re.search(r"```(\w*)", buffer)
                    code_block_end = "```" in buffer[3:] if in_code_block else False

                    if in_code_block and code_block_end:
                        end_pos = buffer.find("```", 3)
                        code_content = buffer[:end_pos]
                        print()
                        console.print(
                            Panel(
                                Syntax(code_content, code_language or "text", theme="monokai", word_wrap=True),
                                border_style="dim",
                            )
                        )
                        buffer = buffer[end_pos + 3 :]
                        in_code_block = False
                    elif not in_code_block and code_block_start:
                        start_pos = code_block_start.start()
                        if start_pos > 0:
                            print(buffer[:start_pos], end="", flush=True)
                        code_language = code_block_start.group(1) or "text"
                        buffer = buffer[code_block_start.end() :]
                        in_code_block = True
                    elif not in_code_block:
                        print(buffer, end="", flush=True)
                        buffer = ""

            print()
            return response_text
        except requests.exceptions.RequestException as exc:
            print(f"[bold red]Request failed:[/bold red] {exc}")
            return ""

    def complete(self, config: AppConfig, messages: list[dict[str, str]]) -> str:
        url = f"{config.base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": False,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.exceptions.RequestException as exc:
            print(f"[bold red]Request failed:[/bold red] {exc}")
            return ""
