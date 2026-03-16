# TermiLLM
A terminal-based LLM chat app that runs locally and interacts with your vLLM server

## Backend Architecture
TermiLLM is a client. It does not run model inference itself.

The intended design is:
- TermiLLM runs as a terminal client in its own Python environment
- The inference backend runs as a separate service
- The two communicate over HTTP using OpenAI-compatible endpoints such as `/v1/models` and `/v1/chat/completions`

This means you can:
- Run vLLM in a different local Python environment
- Run vLLM on another machine and point TermiLLM at it
- Replace vLLM with another OpenAI-compatible backend later

## vLLM Integration
TermiLLM works well with [vLLM](https://github.com/vllm-project/vllm), but vLLM is expected to be started separately from the TermiLLM client. Before using TermiLLM:

1. Install vLLM in a separate environment if needed
2. Start a vLLM server with your preferred model, for example:

```bash
python -m vllm.entrypoints.api_server --model Qwen/Qwen2.5-Coder-3B-Instruct --port 8000
```

For local development, a common setup is:
- terminal A: activate your `vllm` environment and start the vLLM server on port `8000`
- terminal B: activate TermiLLM's environment and run `./run.sh`

## Features
- **Interactive Chat Interface**: Connect to your local vLLM backend with streaming responses
- **User Experience**:
  - Colorful output using Rich for a pleasant terminal experience
  - Keyboard navigation to review chat history
  - Stream responses from your local LLM in real-time
- **Command System**:
  - `/help` - Display available commands
  - `/clear` - Clear the current conversation
  - `/exit` - Exit the application
  - `/model` - Change the model on the fly
  - `/temp` - Adjust temperature setting
  - `/max_tokens` - Change maximum token output
- **Configuration Management**:
  - Persistent settings via JSON configuration file
  - Dynamic model switching without restarting

## Usage
```bash
source ./venv.sh
./run.sh
```

By default, TermiLLM connects to `http://localhost:8000`.

You can also specify a different model or server:
```bash
./run.sh --model Qwen/Qwen2.5-Coder-3B-Instruct --base-url http://localhost:8000
```

If your inference service is already running in another local environment or on another machine, only the `base_url` and model name need to match that backend.

## Configuration
TermiLLM creates a configuration file named `termillm_config.json` in the application directory that stores your settings. You can edit this file directly to customize your preferences:

```json
{
  "model": "Qwen/Qwen2.5-Coder-3B-Instruct",
  "base_url": "http://localhost:8000",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Settings can also be changed from within the application using commands like `/model`, `/temp`, and `/max_tokens`.

## Development Roadmap
Interesting? Feel free to contribute or create a PR for features you want or bugs you found!
The following is the plan:
### V 1.0.0
- [x] Basic Chat Feature
    - [x] Connect to vLLM backend
    - [x] Send/receive message to/from backend
- [x] Support Streamed Output
- [x] Support keyboard move
- [x] Slash Commands
    - [x] /help
    - [x] /clear
    - [x] /exit
- [x] Configurable model
    - [x] Support diff model through vllm
    - [x] Change model use '/model'
    - [x] Save previous model selection
    - [x] Check model (backend connection) before start
- [x] Move setting to JSON
- [x] Colorful Output: Use rich to make UX more pleasant
- [ ] ~~Provided more message during generating~~
- [x] Documentation

### V 1.0.1 (In Progress)
- [x] Restructure the Python app into replaceable modules
- [x] Add a Python MVP agent loop
- [ ] Add confirmation and safety policy for command execution
- [ ] Add pytest
- [ ] CI/CD

### V 1.1.0 (Planned)
- [ ] Highlight the code in output(may use a buffer)
- [ ] Local file support
    - [ ] READ file, such as cpp, py, txt, md
    - [ ] Write to file
    - [ ] Generate file
- [ ] Linux command
- [ ] API Config
- [ ] Integrated vLLM as part of the project
- [ ] Docker

### Future Tasks
- [ ] A LangChain Mode
- [ ] Moving to [bubbletea](https://github.com/charmbracelet/bubbletea) style
- [ ] Integrated local inference into it
- [ ] Integrated model into it
