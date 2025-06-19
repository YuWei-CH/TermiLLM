import argparse
import requests
import json
import os
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich import print
from rich.markdown import Markdown
from prompt_toolkit.formatted_text import HTML

# Use the application directory for the config file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "termillm_config.json")

def load_config():
    """Load configuration from file."""
    config = {
        "model": "meta-llama/Llama-3.2-3B-Instruct",  # Default model
        "base_url": "http://localhost:8000",  # Default URL
        "temperature": 0.7,  # Default temperature
        "max_tokens": 2048  # Default max tokens
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                config.update(saved_config)
            print(f"[dim]Loaded configuration from {CONFIG_FILE}[/dim]")
        else:
            # Create the default config file if it doesn't exist
            save_config(config)
            print(f"[dim]Created default configuration file at {CONFIG_FILE}[/dim]")
    except Exception as e:
        print(f"[yellow]Warning: Failed to load config: {e}[/yellow]")
    
    return config

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[dim]Settings saved to {CONFIG_FILE}[/dim]")
    except Exception as e:
        print(f"[yellow]Warning: Failed to save config: {e}[/yellow]")

def check_model_availability(base_url, model):
    """Check if the vLLM server is accessible and the model is available."""
    try:
        # Try to get the list of models
        models_url = f"{base_url}/v1/models"
        response = requests.get(models_url, timeout=5)
        
        if response.status_code == 200:
            # Server is up and returned models
            models_data = response.json()
            available_models = [model_info["id"] for model_info in models_data.get("data", [])]
            
            if model in available_models:
                return True
            else:
                print(f"[bold yellow]Warning:[/bold yellow] Model '{model}' not found in available models.")
                if available_models:
                    print(f"Available models: {', '.join(available_models)}")
                return False
        
        # If models endpoint didn't work, try a minimal chat request
        chat_url = f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "stream": False
        }
        
        response = requests.post(chat_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            error_message = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_message = error_data["error"].get("message", error_message)
            except:
                pass
            print(f"[bold red]Model check failed:[/bold red] {error_message}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Connection to vLLM server failed:[/bold red] {e}")
        return False

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
    # Load saved config
    config = load_config()
    
    parser = argparse.ArgumentParser(description="Chat with a local vLLM server from terminal.")
    parser.add_argument("--base-url", type=str, default=config["base_url"], 
                        help=f"Base URL of vLLM server (default: {config['base_url']})")
    parser.add_argument("--model", type=str, default=config["model"], 
                        help=f"Model name (default: {config['model']})")
    parser.add_argument("--temperature", type=float, default=config["temperature"], 
                        help=f"Sampling temperature (default: {config['temperature']})")
    parser.add_argument("--max_tokens", type=int, default=config["max_tokens"], 
                        help=f"Maximum model token length (default: {config['max_tokens']})")

    args = parser.parse_args()
    session = PromptSession(history=InMemoryHistory())
    messages = []
    
    # Extract settings from args
    current_model = args.model
    base_url = args.base_url
    temperature = args.temperature
    max_tokens = args.max_tokens
    
    # Update config if command line args changed the defaults
    if (current_model != config["model"] or 
        base_url != config["base_url"] or
        temperature != config["temperature"] or
        max_tokens != config["max_tokens"]):
        
        config["model"] = current_model
        config["base_url"] = base_url
        config["temperature"] = temperature
        config["max_tokens"] = max_tokens
        save_config(config)
        print("[dim]Settings from command line arguments have been saved to config.[/dim]")

    print("[bold green]Welcome to TermiLLM[/bold green]")
    print("[dim]Type '/help' for commands. Use arrow keys for history. Ctrl+C or '/exit' to quit.[/dim]")
    
    # Check if the model is available before starting
    print(f"[dim]Checking connection to {base_url} and availability of model '{current_model}'...[/dim]")
    if not check_model_availability(base_url, current_model):
        print("[bold red]Failed to connect to the vLLM server or the specified model is not available.[/bold red]")
        print("[dim]Make sure the server is running and the model is loaded.[/dim]")
        return  # Exit the program
    
    print("[bold green]Connection successful! Model is available.[/bold green]")

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
- `/temp <temperature>`: Change the temperature (e.g., /temp 0.5)
- `/max_tokens <number>`: Change the maximum tokens (e.g., /max_tokens 4096)
- `/clear`: Clear the chat history
- `/settings`: View current settings
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
                        new_model = user_input[len("/model "):].strip()
                        if new_model:
                            print(f"[dim]Checking availability of model '{new_model}'...[/dim]")
                            if check_model_availability(base_url, new_model):
                                current_model = new_model
                                # Save the new model choice to config
                                config["model"] = current_model
                                save_config(config)
                                print(f"[cyan]Model set to:[/cyan] {current_model}")
                                print(f"[dim]Model preference saved for future sessions.[/dim]")
                            else:
                                print(f"[red]Could not set model to '{new_model}'. Keeping current model: {current_model}[/red]")
                        else:
                            print("[red]Usage: /model <model_name>[/red]")
                    else:
                        print("[red]Usage: /model <model_name>[/red]")
                    continue
                elif command == "/temp":
                    if user_input.strip() == "/temp":
                        print(f"[cyan]Current temperature:[/cyan] {temperature}")
                    elif user_input.startswith("/temp "):
                        try:
                            new_temp = float(user_input[len("/temp "):].strip())
                            if 0 <= new_temp <= 2:
                                temperature = new_temp
                                config["temperature"] = temperature
                                save_config(config)
                                print(f"[cyan]Temperature set to:[/cyan] {temperature}")
                                print(f"[dim]Temperature preference saved for future sessions.[/dim]")
                            else:
                                print("[red]Temperature should be between 0 and 2.[/red]")
                        except ValueError:
                            print("[red]Usage: /temp <float_value> (e.g., /temp 0.8)[/red]")
                    else:
                        print("[red]Usage: /temp <float_value> (e.g., /temp 0.8)[/red]")
                    continue
                elif command == "/max_tokens":
                    if user_input.strip() == "/max_tokens":
                        print(f"[cyan]Current max_tokens:[/cyan] {max_tokens}")
                    elif user_input.startswith("/max_tokens "):
                        try:
                            new_max_tokens = int(user_input[len("/max_tokens "):].strip())
                            if new_max_tokens > 0:
                                max_tokens = new_max_tokens
                                config["max_tokens"] = max_tokens
                                save_config(config)
                                print(f"[cyan]Max tokens set to:[/cyan] {max_tokens}")
                                print(f"[dim]Max tokens preference saved for future sessions.[/dim]")
                            else:
                                print("[red]Max tokens should be a positive integer.[/red]")
                        except ValueError:
                            print("[red]Usage: /max_tokens <int_value> (e.g., /max_tokens 4096)[/red]")
                    else:
                        print("[red]Usage: /max_tokens <int_value> (e.g., /max_tokens 4096)[/red]")
                    continue
                elif command == "/settings":
                    print(Markdown(f"""
### Current Settings:
- **Model**: {current_model}
- **Server URL**: {base_url}
- **Temperature**: {temperature}
- **Max Tokens**: {max_tokens}
"""))
                    continue
                else:
                    print(f"[yellow]Unknown command: {command}[/yellow]")
                    continue

            # Append message and send
            messages.append({"role": "user", "content": user_input})
            stream_chat(base_url, current_model, temperature, max_tokens, messages)

        except KeyboardInterrupt:
            print("\n[bold red]Interrupted. Type '/exit' to quit.[/bold red]")
        except EOFError:
            print("\n[bold red]Session closed.[/bold red]")
            break

if __name__ == "__main__":
    main()