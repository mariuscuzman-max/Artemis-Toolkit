import json
from pathlib import Path

from core.logger import log

CONFIG_PATH = Path("config/artemis.json")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
        config = json.load(file)

    log("Configuration loaded successfully.")
    return config