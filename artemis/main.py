import sys
import time

from core.config_manager import load_config
from core.launcher import (
    run_command,
    run_python_script,
    run_ahk_script,
    open_url,
    open_folder,
)
from core.logger import log
from core.script_registry import get_mode_entries
from core.validator import validate_entry


def execute_entry(entry: dict, config: dict) -> str:
    entry_type = entry.get("type")
    entry_name = entry.get("name", "Unnamed Entry")
    enabled = entry.get("enabled", True)
    delay_after = entry.get("delay_after", 0)
    cwd = entry.get("cwd")

    if not enabled:
        log(f"Skipping disabled entry: {entry_name}", level="WARNING")
        return "skipped"

    if not validate_entry(entry, config):
        log(f"Validation failed for entry: {entry_name}", level="ERROR")
        return "failed"

    log(f"Executing entry: {entry_name} ({entry_type})")

    success = False

    if entry_type == "command":
        command = entry.get("command", [])
        success = run_command(command, cwd=cwd)

    elif entry_type == "python":
        path = entry.get("path", "")
        success = run_python_script(path, cwd=cwd)

    elif entry_type == "ahk":
        path = entry.get("path", "")
        ahk_path = config.get("settings", {}).get("ahk_path", "")
        success = run_ahk_script(path, ahk_path, cwd=cwd)

    elif entry_type == "url":
        url = entry.get("url", "")
        success = open_url(url)

    elif entry_type == "folder":
        path = entry.get("path", "")
        success = open_folder(path)

    else:
        log(f"Unknown entry type: {entry_type}", level="ERROR")
        return "failed"

    if delay_after > 0:
        log(f"Waiting {delay_after} second(s) after '{entry_name}'")
        time.sleep(delay_after)

    return "success" if success else "failed"


def run_mode(config: dict, mode_name: str) -> None:
    entries = get_mode_entries(config, mode_name)

    if not entries:
        log(f"No entries found for mode '{mode_name}'.", level="WARNING")
        return

    log(f"Running mode: {mode_name}")

    summary = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
    }

    for entry in entries:
        result = execute_entry(entry, config)
        summary[result] += 1

    log(
        f"Run summary for mode '{mode_name}': "
        f"{summary['success']} success, "
        f"{summary['failed']} failed, "
        f"{summary['skipped']} skipped."
    )


def get_mode_from_args() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1].lower()

    return "work"


def main():
    log("Artemis started.")
    config = load_config()
    mode_name = get_mode_from_args()
    run_mode(config, mode_name)


if __name__ == "__main__":
    main()