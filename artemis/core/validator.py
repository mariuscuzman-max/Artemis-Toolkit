from pathlib import Path

from core.logger import log


def validate_entry(entry: dict, config: dict) -> bool:
    entry_name = entry.get("name", "Unnamed Entry")
    entry_type = entry.get("type")

    if not entry_type:
        log(f"Entry '{entry_name}' is missing 'type'.", level="ERROR")
        return False

    if entry_type == "command":
        command = entry.get("command")
        if not isinstance(command, list) or not command:
            log(f"Entry '{entry_name}' has invalid or empty 'command'.", level="ERROR")
            return False

    elif entry_type == "python":
        path = entry.get("path", "")
        if not path:
            log(f"Entry '{entry_name}' is missing 'path'.", level="ERROR")
            return False

        if not Path(path).exists():
            log(f"Entry '{entry_name}' points to missing Python script: {path}", level="ERROR")
            return False

    elif entry_type == "ahk":
        path = entry.get("path", "")
        ahk_path = config.get("settings", {}).get("ahk_path", "")

        if not path:
            log(f"Entry '{entry_name}' is missing 'path'.", level="ERROR")
            return False

        if not Path(path).exists():
            log(f"Entry '{entry_name}' points to missing AHK script: {path}", level="ERROR")
            return False

        if not ahk_path:
            log(f"Entry '{entry_name}' cannot run because 'settings.ahk_path' is missing.", level="ERROR")
            return False

        if not Path(ahk_path).exists():
            log(f"Entry '{entry_name}' has invalid AHK executable path: {ahk_path}", level="ERROR")
            return False

    elif entry_type == "url":
        url = entry.get("url", "")
        if not url:
            log(f"Entry '{entry_name}' is missing 'url'.", level="ERROR")
            return False

    elif entry_type == "folder":
        path = entry.get("path", "")
        if not path:
            log(f"Entry '{entry_name}' is missing 'path'.", level="ERROR")
            return False

        if not Path(path).exists():
            log(f"Entry '{entry_name}' points to missing folder: {path}", level="ERROR")
            return False

    else:
        log(f"Entry '{entry_name}' has unknown type: {entry_type}", level="ERROR")
        return False

    cwd = entry.get("cwd")
    if cwd and not Path(cwd).exists():
        log(f"Entry '{entry_name}' has invalid cwd: {cwd}", level="ERROR")
        return False

    return True