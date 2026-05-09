import os
from pathlib import Path


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


def resolve_config_path(value: str | Path) -> Path:
    path_value = str(value).strip()
    downloads_folder = str(get_default_downloads_folder())
    desktop_folder = str(get_default_desktop_folder())
    repo_root = str(get_repo_root())

    path_value = path_value.replace("{downloads}", downloads_folder)
    path_value = path_value.replace("{Downloads}", downloads_folder)
    path_value = path_value.replace("{desktop}", desktop_folder)
    path_value = path_value.replace("{Desktop}", desktop_folder)
    path_value = path_value.replace("{repo}", repo_root)
    path_value = path_value.replace("{Repo}", repo_root)
    path_value = os.path.expandvars(path_value)

    resolved_path = Path(path_value).expanduser()

    if not resolved_path.is_absolute():
        resolved_path = get_repo_root() / resolved_path

    return resolved_path
