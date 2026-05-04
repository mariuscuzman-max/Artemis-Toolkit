import json
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT_DIR / "runtime"
RECENT_ACTIVITY_FILE = RUNTIME_DIR / "recent_activity.json"


def load_recent_activity() -> dict:
    if not RECENT_ACTIVITY_FILE.exists():
        return {"items": []}

    try:
        data = json.loads(RECENT_ACTIVITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}

    if not isinstance(data, dict):
        return {"items": []}

    items = data.get("items", [])

    if not isinstance(items, list):
        items = []

    return {"items": items}


def save_recent_activity(data: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_ACTIVITY_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def record_recent_activity(
    action: str,
    source_path: str,
    destination_path: str = "",
    detail: str = "",
) -> None:
    data = load_recent_activity()
    items = data.get("items", [])

    display_path = destination_path or source_path
    file_name = Path(display_path).name if display_path else "Unknown file"

    items.insert(0, {
        "timestamp": time.time(),
        "action": action,
        "file_name": file_name,
        "source_path": source_path,
        "destination_path": destination_path,
        "detail": detail,
    })

    data["items"] = items[:20]
    save_recent_activity(data)


def get_recent_activity(limit: int = 3) -> list[dict]:
    data = load_recent_activity()
    items = data.get("items", [])

    valid_items = [
        item for item in items
        if isinstance(item, dict)
    ]

    valid_items.sort(
        key=lambda item: item.get("timestamp", 0),
        reverse=True,
    )

    return valid_items[:limit]