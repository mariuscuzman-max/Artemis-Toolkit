import json
import os
import shutil
import sys
from pathlib import Path


APP_NAME = "Artemis Toolkit"


DEFAULT_DOWNLOADS_SORTER_CONFIG = {
    "first_run_completed": False,
    "watch_folder": "{downloads}",
    "destination_root": "{downloads}\\Sorted",
    "skip_memory_days": 7,
    "processed_memory_days": 30,
    "ignored_exact_names": [
        "desktop.ini",
        "thumbs.db",
        "ehthumbs.db",
        ".ds_store",
    ],
    "cleanup": {
        "min_age_seconds": 604800,
        "min_total_size_mb": 10,
    },
    "user_rules": {
        "enabled": True,
        "rules": [],
    },
    "ignored_extensions": [
        ".tmp",
        ".lock",
        ".crdownload",
        ".part",
        ".download",
        ".opdownload",
        ".!ut",
        ".!qb",
        ".bc!",
        ".filepart",
    ],
    "ignored_prefixes": [
        "~$",
        ".~",
    ],
    "archive_extensions": [
        ".zip",
        ".rar",
        ".7z",
    ],
    "process_existing_on_startup": True,
    "stability_wait_seconds": 2,
    "min_file_age_seconds": 5,
    "categories": {
        "Images": [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".gif",
            ".bmp",
        ],
        "Torrents": [
            ".torrent",
        ],
        "Documents": [
            ".pdf",
            ".docx",
            ".doc",
            ".txt",
            ".xlsx",
            ".xls",
            ".pptx",
        ],
        "Video": [
            ".mp4",
            ".mkv",
            ".avi",
            ".mov",
            ".webm",
        ],
        "Audio": [
            ".mp3",
            ".wav",
            ".flac",
            ".ogg",
        ],
        "Installers": [
            ".exe",
            ".msi",
        ],
        "Subtitles": [
            ".srt",
            ".sub",
        ],
        "Other": [],
    },
    "unknown_category": "Other",
}


def get_default_downloads_folder() -> Path:
    user_profile = os.environ.get("USERPROFILE")

    if user_profile:
        return Path(user_profile) / "Downloads"

    return Path.home() / "Downloads"


def get_default_desktop_folder() -> Path:
    user_profile = os.environ.get("USERPROFILE")

    if user_profile:
        return Path(user_profile) / "Desktop"

    return Path.home() / "Desktop"


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_resource_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)

    if bundled_root:
        return Path(bundled_root)

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return get_repo_root()


def get_resource_path(*parts: str) -> Path:
    return get_resource_root().joinpath(*parts)


def get_app_data_root() -> Path:
    override = os.environ.get("ARTEMIS_APPDATA_DIR")

    if override:
        return Path(override)

    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:
        return Path(local_app_data) / APP_NAME

    return Path.home() / "AppData" / "Local" / APP_NAME


def get_user_config_dir() -> Path:
    return get_app_data_root() / "config"


def get_user_logs_dir() -> Path:
    return get_app_data_root() / "logs"


def get_user_runtime_dir() -> Path:
    return get_app_data_root() / "runtime"


def get_default_sorter_config_template_path() -> Path:
    return get_resource_path("config", "downloads_sorter.json")


def get_sorter_config_path() -> Path:
    config_path = get_user_config_dir() / "downloads_sorter.json"
    ensure_sorter_config_exists(config_path)
    return config_path


def ensure_sorter_config_exists(config_path: Path | None = None) -> Path:
    if config_path is None:
        config_path = get_user_config_dir() / "downloads_sorter.json"

    if config_path.exists():
        return config_path

    config_path.parent.mkdir(parents=True, exist_ok=True)
    template_path = get_default_sorter_config_template_path()

    if template_path.exists():
        shutil.copyfile(template_path, config_path)
    else:
        config_path.write_text(
            json.dumps(DEFAULT_DOWNLOADS_SORTER_CONFIG, indent=2),
            encoding="utf-8",
        )

    return config_path


def resolve_config_path(value: str | Path) -> Path:
    path_value = str(value).strip()
    downloads_folder = str(get_default_downloads_folder())
    desktop_folder = str(get_default_desktop_folder())
    repo_root = str(get_resource_root())
    app_data_root = str(get_app_data_root())

    path_value = path_value.replace("{downloads}", downloads_folder)
    path_value = path_value.replace("{Downloads}", downloads_folder)
    path_value = path_value.replace("{desktop}", desktop_folder)
    path_value = path_value.replace("{Desktop}", desktop_folder)
    path_value = path_value.replace("{repo}", repo_root)
    path_value = path_value.replace("{Repo}", repo_root)
    path_value = path_value.replace("{appdata}", app_data_root)
    path_value = path_value.replace("{AppData}", app_data_root)
    path_value = os.path.expandvars(path_value)

    resolved_path = Path(path_value).expanduser()

    if not resolved_path.is_absolute():
        resolved_path = get_resource_root() / resolved_path

    return resolved_path
