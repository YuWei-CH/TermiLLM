# TermiLLM
A terminal-based LLM chat app that runs locally and interacts with your vLLM server

## Features
- Stream responses from your local LLM
- Command-based interface with history navigation
- Change models on the fly
- Persistent configuration via editable JSON file

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
