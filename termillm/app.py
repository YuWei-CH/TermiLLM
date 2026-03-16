from __future__ import annotations

import argparse

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from rich import print

from termillm.agent import AgentSession
from termillm.config import CONFIG_FILE, AppConfig
from termillm.model_client import ChatModelClient


def build_arg_parser(config: AppConfig) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chat with a local vLLM server from terminal.")
    parser.add_argument(
        "--base-url",
        type=str,
        default=config.base_url,
        help=f"Base URL of vLLM server (default: {config.base_url})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.model,
        help=f"Model name (default: {config.model})",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=config.temperature,
        help=f"Sampling temperature (default: {config.temperature})",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=config.max_tokens,
        help=f"Maximum model token length (default: {config.max_tokens})",
    )
    return parser


def apply_cli_overrides(config: AppConfig, args: argparse.Namespace) -> bool:
    changed = (
        config.model != args.model
        or config.base_url != args.base_url
        or config.temperature != args.temperature
        or config.max_tokens != args.max_tokens
    )
    config.model = args.model
    config.base_url = args.base_url
    config.temperature = args.temperature
    config.max_tokens = args.max_tokens
    return changed


def run() -> int:
    config_existed = CONFIG_FILE.exists()
    config = AppConfig.load()
    if config_existed:
        print(f"[dim]Loaded configuration from {CONFIG_FILE}[/dim]")
    else:
        print(f"[dim]Created default configuration file at {CONFIG_FILE}[/dim]")

    parser = build_arg_parser(config)
    args = parser.parse_args()

    if apply_cli_overrides(config, args):
        config.save()
        print("[dim]Settings from command line arguments have been saved to config.[/dim]")

    client = ChatModelClient()
    session = AgentSession(config=config, client=client)
    prompt_session = PromptSession(history=InMemoryHistory())

    print("[bold green]Welcome to TermiLLM[/bold green]")
    print("[dim]Type '/help' for commands. Use arrow keys for history. Ctrl+C or '/exit' to quit.[/dim]")
    print(f"[dim]Checking connection to {config.base_url} and availability of model '{config.model}'...[/dim]")
    if not client.check_model_availability(config):
        print("[bold red]Failed to connect to the vLLM server or the specified model is not available.[/bold red]")
        print("[dim]Make sure the server is running and the model is loaded.[/dim]")
        return 1

    print("[bold green]Connection successful! Model is available.[/bold green]")

    while True:
        try:
            user_input = prompt_session.prompt(HTML("<ansiblue><b>You:</b></ansiblue> "))
            if session.handle_input(user_input):
                return 0
        except KeyboardInterrupt:
            print("\n[bold red]Interrupted. Type '/exit' to quit.[/bold red]")
        except EOFError:
            print("\n[bold red]Session closed.[/bold red]")
            return 0


def main() -> int:
    return run()

