# TermiLLM
A terminal-based LLM chat app that runs locally and interacts with your vLLM server

## vLLM Integration
TermiLLM relies on [vLLM](https://github.com/vllm-project/vllm), a high-throughput and memory-efficient inference engine for LLMs. Before using TermiLLM:

1. Install vLLM: `pip install vllm`
2. Start a vLLM server with your preferred model: `python -m vllm.entrypoints.api_server --model meta-llama/Llama-3.2-3B-Instruct --port 8000`

Future versions of TermiLLM will include integrated vLLM support, eliminating the need for a separate server.

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
python3 TermiLLM.py
```

You can also specify a different model or server:
```bash
python3 TermiLLM.py --model meta-llama/Llama-3.2-3B-Instruct --base-url http://localhost:8000
```

## Configuration
TermiLLM creates a configuration file named `termillm_config.json` in the application directory that stores your settings. You can edit this file directly to customize your preferences:

```json
{
  "model": "meta-llama/Llama-3.2-3B-Instruct",
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
    - [ ] Check model (backend connection) before start
- [x] Move setting to JSON
- [x] Colorful Output: Use rich to make UX more pleasant
- [ ] ~~Provided more message during generating~~
- [x] Documentation

### V 1.0.1 (In Progress)
- [ ] C++ version
- [ ] Convert current TermiLLM.py as an engine
- [ ] Prefer to build a python interface for user and connect to the engine
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
