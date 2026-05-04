import os
import sys
import subprocess
from pathlib import Path
import psutil
import json
import time
ROOT_DIR = Path(__file__).resolve().parents[2]

RUNTIME_DIR = ROOT_DIR / "runtime"
LOCK_FILE = RUNTIME_DIR / "artemis.lock"
PID_FILE = RUNTIME_DIR / "artemis.pid"
STOP_FILE = RUNTIME_DIR / "artemis.stop"

SORTER_SCRIPT = ROOT_DIR / "scripts/python/downloads_auto_sorter.py"
ACTIVITY_FILE = RUNTIME_DIR / "artemis_activity.json"

def is_artemis_running() -> bool:
    if not PID_FILE.exists():
        return False

    try:
        pid = int(PID_FILE.read_text().strip())
    except Exception:
        return False

    if not psutil.pid_exists(pid):
        return False

    try:
        process = psutil.Process(pid)
        cmdline = " ".join(process.cmdline()).lower()

        return (
            "downloads_auto_sorter.py" in cmdline
            or "scripts.python.downloads_auto_sorter" in cmdline
        )

    except Exception:
        return False

def get_artemis_activity() -> dict:
    if not ACTIVITY_FILE.exists():
        return {
            "state": "idle",
            "message": "",
            "timestamp": 0,
        }

    try:
        return json.loads(ACTIVITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "state": "error",
            "message": "Invalid activity state",
            "timestamp": time.time(),
        }

def start_artemis():
    if is_artemis_running():
        print("Artemis already running.")
        return

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    if STOP_FILE.exists():
        STOP_FILE.unlink()

    subprocess.Popen(
        [sys.executable, "-m", "scripts.python.downloads_auto_sorter"],
        cwd=str(ROOT_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    print("Artemis started.")

def stop_artemis():
    if not is_artemis_running():
        print("Artemis not running.")
        return

    STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    STOP_FILE.touch()

    print("Stop signal sent.")