import argparse
import requests
import json
from rich import print
from rich.prompt import Prompt

def chat_with_model(base_url, model, temperature, max_tokens):
    print("[bold green]Welcome to TermiLLM! Type your message. (Type 'exit' to quit.)[/bold green]")
    
    while True:
        user_input = Prompt.ask("[bold blue]You[/bold blue]")
        
        if user_input.strip().lower() == "exit":
            print("[bold red]Goodbye![/bold red]")
            break
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": user_input}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            response.raise_for_status()
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            print(f"[bold magenta]Assistant:[/bold magenta] {reply}")
        
        except requests.exceptions.RequestException as e:
            print(f"[bold red]Request failed:[/bold red] {e}")

def main():
    parser = argparse.ArgumentParser(description="Chat with a local vLLM server from terminal.")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000", help="Base URL of vLLM server")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.2-3B-Instruct", help="Model name")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--max_tokens", type=int, default=2048, help="Maximum model token length")

    args = parser.parse_args()

    chat_with_model(args.base_url, args.model, args.temperature, args.max_tokens)

if __name__ == "__main__":
    main()