import time


DEFAULT_CLEANUP_MIN_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days
DEFAULT_CLEANUP_MIN_TOTAL_SIZE_MB = 10


def get_cleanup_rules(config: dict) -> dict:
    """
    Reads cleanup rules from config and applies safe defaults.
    """
    cleanup_config = config.get("cleanup", {})

    return {
        "min_age_seconds": cleanup_config.get(
            "min_age_seconds",
            DEFAULT_CLEANUP_MIN_AGE_SECONDS,
        ),
        "min_total_size_mb": cleanup_config.get(
            "min_total_size_mb",
            DEFAULT_CLEANUP_MIN_TOTAL_SIZE_MB,
        ),
    }


def is_cleanup_item_old_enough(item: dict, min_age_seconds: int, now: float | None = None) -> bool:
    """
    Checks if one cleanup item is old enough to be considered.
    Age is checked per item.
    """
    if now is None:
        now = time.time()

    timestamp = item.get("timestamp", 0)

    try:
        timestamp = float(timestamp)
    except (TypeError, ValueError):
        return False

    return now - timestamp >= min_age_seconds


def get_cleanup_candidates_by_threshold(items: list[dict], config: dict) -> list[dict]:
    """
    Cleanup threshold logic.

    Rule:
    - First, keep only items older than min_age_seconds.
    - Then, add their sizes together.
    - Only return candidates if total old-item size >= min_total_size_mb.

    This prevents spam, but still catches many small old files as clutter.
    """
    rules = get_cleanup_rules(config)

    min_age_seconds = rules["min_age_seconds"]
    min_total_size_bytes = rules["min_total_size_mb"] * 1024 * 1024

    now = time.time()

    old_items = [
        item for item in items
        if is_cleanup_item_old_enough(item, min_age_seconds, now)
    ]

    total_size = 0

    for item in old_items:
        try:
            total_size += int(item.get("size", 0))
        except (TypeError, ValueError):
            continue

    if total_size >= min_total_size_bytes:
        return old_items

    return []