import time
from pathlib import Path

from artemis.core.path_utils import resolve_config_path


DEFAULT_CLEANUP_MIN_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days
DEFAULT_CLEANUP_MIN_TOTAL_SIZE_MB = 10

SUPPORTED_RULE_MATCH_TYPES = {"extension", "name_contains"}
SUPPORTED_RULE_ACTION_TYPES = {"move_to", "skip"}


# ============================================================
# CLEANUP RULES
# ============================================================

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


def is_cleanup_item_old_enough(
    item: dict,
    min_age_seconds: int,
    now: float | None = None,
) -> bool:
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


# ============================================================
# USER RULES PREPARATION — v0.4.0
# ============================================================

def get_user_rules_config(config: dict) -> dict:
    """
    Reads the user_rules section safely.

    This does not execute rules.
    It only prepares them for later sorter integration.
    """
    user_rules_config = config.get("user_rules", {})

    if not isinstance(user_rules_config, dict):
        return {
            "enabled": False,
            "rules": [],
        }

    enabled = user_rules_config.get("enabled", True)
    rules = user_rules_config.get("rules", [])

    if not isinstance(rules, list):
        rules = []

    return {
        "enabled": bool(enabled),
        "rules": rules,
    }


def normalize_extension(value: str) -> str:
    """
    Normalizes extensions into lowercase '.ext' format.
    Example: 'PDF' -> '.pdf'
    """
    value = value.strip().lower()

    if not value:
        return ""

    if not value.startswith("."):
        value = "." + value

    return value


def normalize_rule_condition(condition: dict) -> dict | None:
    if not isinstance(condition, dict):
        return None

    match_type = condition.get("type")
    match_value = condition.get("value", "")

    if match_type not in SUPPORTED_RULE_MATCH_TYPES:
        return None

    if not isinstance(match_value, str):
        return None

    if match_type == "extension":
        match_value = normalize_extension(match_value)
        if not match_value:
            return None

    elif match_type == "name_contains":
        match_value = match_value.strip().lower()
        if not match_value:
            return None

    return {
        "type": match_type,
        "value": match_value,
    }


def get_rule_conditions(rule: dict) -> list[dict]:
    conditions = rule.get("conditions")

    if isinstance(conditions, list):
        normalized_conditions = []
        seen_condition_keys = set()

        for condition in conditions:
            normalized_condition = normalize_rule_condition(condition)

            if normalized_condition is None:
                return []

            condition_key = (
                normalized_condition["type"],
                normalized_condition["value"],
            )

            if condition_key in seen_condition_keys:
                return []

            seen_condition_keys.add(condition_key)
            normalized_conditions.append(normalized_condition)

        return normalized_conditions

    match = rule.get("match", {})
    normalized_match = normalize_rule_condition(match)

    if normalized_match is None:
        return []

    return [normalized_match]


def normalize_user_rule(rule: dict) -> dict | None:
    """
    Converts one raw JSON rule into a predictable internal structure.

    Invalid rules return None.
    v0.4.0 is intentionally forgiving:
    bad rules are ignored instead of crashing the sorter.
    """
    if not isinstance(rule, dict):
        return None

    if not rule.get("enabled", True):
        return None

    action = rule.get("action", {})

    if not isinstance(action, dict):
        return None

    action_type = action.get("type")

    if action_type not in SUPPORTED_RULE_ACTION_TYPES:
        return None

    conditions = get_rule_conditions(rule)

    if not conditions:
        return None

    normalized_action = {
        "type": action_type,
    }

    if action_type == "move_to":
        destination = action.get("destination", "")

        if not isinstance(destination, str) or not destination.strip():
            return None

        normalized_action["destination"] = destination.strip()

    return {
        "id": rule.get("id", ""),
        "name": rule.get("name", "Unnamed rule"),
        "conditions": conditions,
        "match": conditions[0],
        "action": normalized_action,
    }

def validate_user_rules_config(config: dict) -> list[str]:
    """
    Validates user_rules config for diagnostics.

    Important:
    - Does not move files.
    - Does not crash the sorter.
    - Returns warning messages only.
    """
    warnings = []

    user_rules_config = config.get("user_rules", {})

    if not isinstance(user_rules_config, dict):
        return ["user_rules ignored: section must be an object."]

    global_enabled = user_rules_config.get("enabled", True)

    if not isinstance(global_enabled, bool):
        warnings.append(
            "user_rules.enabled should be true or false. Non-boolean value found."
        )

    rules = user_rules_config.get("rules", [])

    if not isinstance(rules, list):
        return ["user_rules.rules ignored: rules must be a list."]

    seen_ids = set()

    for index, rule in enumerate(rules):
        label = f"user_rules.rules[{index}]"

        if not isinstance(rule, dict):
            warnings.append(f"{label} ignored: rule must be an object.")
            continue

        rule_id = rule.get("id", "")

        if not isinstance(rule_id, str) or not rule_id.strip():
            warnings.append(f"{label} warning: rule has missing/empty id.")
        elif rule_id in seen_ids:
            warnings.append(f"{label} warning: duplicate rule id '{rule_id}'.")
        else:
            seen_ids.add(rule_id)

        rule_enabled = rule.get("enabled", True)

        if not isinstance(rule_enabled, bool):
            warnings.append(
                f"{label} ignored: enabled must be true or false."
            )
            continue

        if rule_enabled is False:
            continue

        action = rule.get("action", {})

        if not isinstance(action, dict):
            warnings.append(f"{label} ignored: action must be an object.")
            continue

        raw_conditions = rule.get("conditions")

        if isinstance(raw_conditions, list):
            if not raw_conditions:
                warnings.append(f"{label} ignored: conditions must not be empty.")
                continue

            seen_condition_keys = set()

            for condition_index, condition in enumerate(raw_conditions):
                condition_label = f"{label}.conditions[{condition_index}]"

                if not isinstance(condition, dict):
                    warnings.append(f"{condition_label} ignored: condition must be an object.")
                    continue

                normalized_condition = normalize_rule_condition(condition)

                if normalized_condition is None:
                    warnings.append(f"{condition_label} ignored: invalid condition.")
                    continue

                condition_key = (
                    normalized_condition["type"],
                    normalized_condition["value"],
                )

                if condition_key in seen_condition_keys:
                    warnings.append(f"{condition_label} ignored: duplicate condition.")
                    continue

                seen_condition_keys.add(condition_key)

            if not get_rule_conditions(rule):
                warnings.append(f"{label} ignored: no valid conditions found.")
                continue

        else:
            match = rule.get("match", {})

            if not isinstance(match, dict):
                warnings.append(f"{label} ignored: match must be an object.")
                continue

            normalized_match = normalize_rule_condition(match)

            if normalized_match is None:
                warnings.append(f"{label} ignored: invalid match.")
                continue

        action_type = action.get("type")

        if action_type == "delete":
            warnings.append(
                f"{label} ignored: delete action is not supported. "
                "Artemis never deletes automatically."
            )
            continue

        if action_type not in SUPPORTED_RULE_ACTION_TYPES:
            warnings.append(
                f"{label} ignored: unsupported action type '{action_type}'."
            )
            continue

        if action_type == "move_to":
            destination = action.get("destination", "")

            if not isinstance(destination, str) or not destination.strip():
                warnings.append(
                    f"{label} ignored: move_to requires a destination folder."
                )
                continue

            destination_path = resolve_config_path(destination)

            if not destination_path.exists() or not destination_path.is_dir():
                warnings.append(
                    f"{label} warning: destination folder does not exist. "
                    "Rule will fall back to default sorting."
                )

    return warnings

def get_active_user_rules(config: dict) -> list[dict]:
    """
    Returns active, normalized user rules.

    Safe behavior:
    - Missing config = no rules.
    - Disabled user_rules = no rules.
    - Broken rule entries are ignored.
    """
    user_rules_config = get_user_rules_config(config)

    if not user_rules_config["enabled"]:
        return []

    active_rules = []

    for rule in user_rules_config["rules"]:
        normalized_rule = normalize_user_rule(rule)

        if normalized_rule is not None:
            active_rules.append(normalized_rule)

    return active_rules


def rule_matches_file(rule: dict, file_path: Path) -> bool:
    """
    Checks whether a prepared user rule matches a file.

    This only answers yes/no.
    It does not move, skip, or modify anything.
    """
    conditions = get_rule_conditions(rule)

    if not conditions:
        return False

    return all(rule_condition_matches_file(condition, file_path) for condition in conditions)


def rule_condition_matches_file(condition: dict, file_path: Path) -> bool:
    match_type = condition.get("type")
    match_value = condition.get("value")

    if match_type == "extension":
        return file_path.suffix.lower() == match_value

    if match_type == "name_contains":
        return match_value in file_path.name.lower()

    return False


def find_first_matching_user_rule(file_path: Path, config: dict) -> dict | None:
    """
    Finds the first active user rule matching the file.

    This prepares us for v0.4.1, where the sorter will actually use this.
    """
    for rule in get_active_user_rules(config):
        if rule_matches_file(rule, file_path):
            return rule

    return None
