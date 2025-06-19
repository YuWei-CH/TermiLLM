import argparse
import requests
import json
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print
from rich.markdown import Markdown
from prompt_toolkit.formatted_text import HTML

def stream_chat(base_url, model, temperature, max_tokens, messages):
    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }

    try:
        with requests.post(url, headers=headers, json=payload, stream=True) as resp:
            resp.raise_for_status()
            print("[bold magenta]Assistant:[/bold magenta] ", end="", flush=True)
            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data = line[len("data: "):].strip()
                    if data == "[DONE]":
                        continue
                    try:
                        content = json.loads(data)
                        delta = content.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        print(delta, end="", flush=True)
                    except json.JSONDecodeError:
                        # Skip lines that are not valid JSON
                        continue
            print()
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Request failed:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Chat with a local vLLM server from terminal.")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL of vLLM server")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.2-3B-Instruct", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--max_tokens", type=int, default=2048, help="Maximum model token length")

    args = parser.parse_args()
    session = PromptSession(history=InMemoryHistory())
    messages = []
    current_model = args.model

    print("[bold green]Welcome to TermiLLM[/bold green]")
    print("[dim]Type '/help' for commands. Use arrow keys for history. Ctrl+C or '/exit' to quit.[/dim]")

    while True:
        try:
            user_input = session.prompt(HTML("<ansiblue><b>You:</b></ansiblue> "))

            # Handle slash commands
            if user_input.startswith("/"):
                parts = user_input.strip().split(maxsplit=1)
                command = parts[0]

                if command == "/exit":
                    print("[bold red]Exiting...[/bold red]")
                    break
                elif command == "/help":
                    print(Markdown("""
### Commands:
- `/model <model>`: Change the model (e.g., /model deepseek-ai/deepseek-llm-7b-chat)
- `/clear`: Clear the chat history
- `/exit`: Exit the application
"""))
                    continue
                elif command == "/clear":
                    messages.clear()
                    print("[green]Conversation history cleared.[/green]")
                    continue
                elif command == "/model":
                    if user_input.strip() == "/model":
                        print(f"[cyan]Current model:[/cyan] {current_model}")
                    elif user_input.startswith("/model "):
                        current_model = user_input[len("/model "):].strip()
                        if current_model:
                            print(f"[cyan]Model set to:[/cyan] {current_model}")
                        else:
                            print("[red]Usage: /model <model_name>[/red]")
                    else:
                        print("[red]Usage: /model <model_name>[/red]")
                    continue
                else:
                    print(f"[yellow]Unknown command: {command}[/yellow]")
                    continue

            # Append message and send
            messages.append({"role": "user", "content": user_input})
            stream_chat(args.base_url, current_model, args.temperature, args.max_tokens, messages)

        except KeyboardInterrupt:
            print("\n[bold red]Interrupted. Type '/exit' to quit.[/bold red]")
        except EOFError:
            print("\n[bold red]Session closed.[/bold red]")
            break

if __name__ == "__main__":
    main()