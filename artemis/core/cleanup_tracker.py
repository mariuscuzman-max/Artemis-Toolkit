import json
import time
from pathlib import Path

from artemis.core.path_utils import get_sorter_config_path, get_user_runtime_dir
from artemis.core.rules_engine import get_cleanup_candidates_by_threshold



RUNTIME_DIR = get_user_runtime_dir()
CLEANUP_FILE = RUNTIME_DIR / "cleanup_queue.json"


def load_cleanup():
    if not CLEANUP_FILE.exists():
        return {"items": []}

    try:
        return json.loads(CLEANUP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}


def save_cleanup(data):
    CLEANUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLEANUP_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_cleanup_item(path: str, size: int, reason: str):
    data = load_cleanup()

    existing_paths = {item.get("path") for item in data.get("items", [])}

    if path in existing_paths:
        return

    data["items"].append({
        "path": path,
        "size": size,
        "reason": reason,
        "timestamp": time.time(),
    })

    save_cleanup(data)


def get_cleanup_stats():
    data = load_cleanup()

    total_size = sum(item.get("size", 0) for item in data.get("items", []))
    count = len(data.get("items", []))

    return count, total_size

CONFIG_FILE = get_sorter_config_path()


def load_cleanup_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}

    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def get_cleanup_candidates(config: dict | None = None):
    data = load_cleanup()
    items = data.get("items", [])

    if config is None:
        config = load_cleanup_config()

    return get_cleanup_candidates_by_threshold(items, config)


def postpone_cleanup_items(paths: list[str]) -> None:
    data = load_cleanup()
    now = time.time()
    path_set = set(paths)

    for item in data.get("items", []):
        if item.get("path") in path_set:
            item["timestamp"] = now

    save_cleanup(data)
    
def clean_invalid_items() -> None:
    data = load_cleanup()

    valid_items = []

    for item in data.get("items", []):
        path = item.get("path")

        if path and Path(path).exists():
            valid_items.append(item)

    if len(valid_items) != len(data.get("items", [])):
        data["items"] = valid_items
        save_cleanup(data)
        
def remove_cleanup_items(paths: list[str]) -> None:
    data = load_cleanup()
    path_set = set(paths)

    data["items"] = [
        item for item in data.get("items", [])
        if item.get("path") not in path_set
    ]

    save_cleanup(data)        


def delete_cleanup_items(candidates: list[dict]) -> dict:
    data = load_cleanup()

    deleted = 0
    failed = 0

    remaining_items = []

    candidate_paths = {item.get("path") for item in candidates}

    for item in data.get("items", []):
        path_str = item.get("path")
        path = Path(path_str) if path_str else None

        if path_str in candidate_paths:
            try:
                if path and path.exists() and path.is_file():
                    path.unlink()
                    deleted += 1
                # chiar dacă nu există → îl scoatem din queue
            except Exception:
                failed += 1
                remaining_items.append(item)
        else:
            remaining_items.append(item)

    data["items"] = remaining_items
    save_cleanup(data)

    return {
        "deleted": deleted,
        "failed": failed,
    }
