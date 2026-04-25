from core.logger import log


def get_mode_entries(config: dict, mode_name: str) -> list[dict]:
    modes = config.get("modes", {})
    entries = modes.get(mode_name, [])

    if not isinstance(entries, list):
        log(f"Mode '{mode_name}' is not a valid list in config.", level="ERROR")
        return []

    log(f"Loaded {len(entries)} entries for mode '{mode_name}'.")
    return entries