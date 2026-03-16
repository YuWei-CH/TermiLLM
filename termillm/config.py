from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = APP_ROOT / "termillm_config.json"


@dataclass
class AppConfig:
    model: str = "Qwen/Qwen2.5-Coder-3B-Instruct"
    base_url: str = "http://localhost:8000"
    temperature: float = 0.7
    max_tokens: int = 2048

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "AppConfig":
        config = cls()
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                config_data = json.load(handle)
            for field_name in asdict(config):
                if field_name in config_data:
                    setattr(config, field_name, config_data[field_name])
        else:
            config.save(path)
        return config

    def save(self, path: Path = CONFIG_FILE) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=2)
