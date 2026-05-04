import subprocess
import sys
from pathlib import Path

LOCK_FILE = Path("logs/downloads_sorter.lock")

SORTER_PATH = "scripts/python/downloads_auto_sorter.py"


def is_running():
    return LOCK_FILE.exists()


def start():
    if is_running():
        print("Sorter already running.")
        return

    subprocess.Popen(["python", SORTER_PATH])
    print("Sorter started.")


def stop():
    if not is_running():
        print("Sorter not running.")
        return

    # metoda simplă: ștergi lock → sorter se oprește la următorul loop dacă verifici
    LOCK_FILE.unlink(missing_ok=True)
    print("Stop signal sent.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sorter_control.py [start|stop|status]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        print("Running" if is_running() else "Stopped")