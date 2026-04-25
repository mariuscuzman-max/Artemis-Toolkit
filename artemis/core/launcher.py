import subprocess
import webbrowser
from pathlib import Path

from core.logger import log


def run_command(command: list[str], cwd: str | None = None) -> bool:
    try:
        subprocess.Popen(command, cwd=cwd)
        log(f"Launch success: {command}" + (f" | cwd={cwd}" if cwd else ""))
        return True
    except Exception as error:
        log(f"Launch failed: {command} | Error: {error}", level="ERROR")
        return False


def run_python_script(script_path: str, cwd: str | None = None) -> bool:
    path = Path(script_path)

    if not path.exists():
        log(f"Python script not found: {script_path}", level="ERROR")
        return False

    return run_command(["python", str(path)], cwd=cwd)


def run_ahk_script(script_path: str, ahk_path: str, cwd: str | None = None) -> bool:
    script = Path(script_path)
    ahk = Path(ahk_path)

    if not script_path:
        log("AHK script path is empty.", level="ERROR")
        return False

    if not script.exists():
        log(f"AHK script not found: {script_path}", level="ERROR")
        return False

    if not ahk_path:
        log("AHK executable path is empty.", level="ERROR")
        return False

    if not ahk.exists():
        log(f"AHK executable not found: {ahk_path}", level="ERROR")
        return False

    return run_command([str(ahk), str(script)], cwd=cwd)


def open_url(url: str) -> bool:
    try:
        webbrowser.open(url)
        log(f"Opened URL: {url}")
        return True
    except Exception as error:
        log(f"Failed to open URL: {url} | Error: {error}", level="ERROR")
        return False


def open_folder(path: str) -> bool:
    try:
        subprocess.Popen(["explorer", path])
        log(f"Opened folder: {path}")
        return True
    except Exception as error:
        log(f"Failed to open folder: {path} | Error: {error}", level="ERROR")
        return False