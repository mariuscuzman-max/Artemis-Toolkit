from email import message
import json
import os
import shutil
import sys
import time
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import messagebox
from artemis.core.cleanup_tracker import clean_invalid_items

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ROOT_DIR = Path(__file__).resolve().parents[2]
ARTEMIS_DIR = ROOT_DIR / "artemis"

from artemis.core.cleanup_tracker import add_cleanup_item

CONFIG_PATH = ROOT_DIR / "config/downloads_sorter.json"
LOG_FILE = ROOT_DIR / "logs/downloads_sorter.log"
STATE_FILE = ROOT_DIR / "logs/downloads_sorter_state.json"

RUNTIME_DIR = ROOT_DIR / "runtime"
LOCK_FILE = RUNTIME_DIR / "artemis.lock"
PID_FILE = RUNTIME_DIR / "artemis.pid"
STOP_FILE = RUNTIME_DIR / "artemis.stop"
ACTIVITY_FILE = RUNTIME_DIR / "artemis_activity.json"


def log(message: str, level: str = "INFO") -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"
    print(line)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")

_last_state = {"state": None, "message": None}

def write_activity_state(state: str, message: str = "") -> None:
    try:
        if ACTIVITY_FILE.exists():
            existing = json.loads(ACTIVITY_FILE.read_text(encoding="utf-8"))

            if (
                existing.get("state") == state and
                existing.get("message") == message
            ):
                return
    except Exception:
        pass
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

        payload = {
            "state": state,
            "message": message,
            "timestamp": time.time(),
        }

        ACTIVITY_FILE.write_text(json.dumps(payload), encoding="utf-8")

    except Exception as error:
        log(f"Failed to write activity state: {error}", level="WARNING")



def write_activity_state(state: str, message: str = "") -> None:
    
    
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

        payload = {
            "state": state,
            "message": message,
            "timestamp": time.time(),
        }

        ACTIVITY_FILE.write_text(json.dumps(payload), encoding="utf-8")

    except Exception as error:
        log(f"Failed to write activity state: {error}", level="WARNING")
        
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "skipped_archives": [],
            "processed_archives": [],
        }

    with STATE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)


def get_file_key(file_path: Path) -> str:
    try:
        stat = file_path.stat()
        return f"{file_path.name}_{stat.st_size}_{stat.st_mtime_ns}"
    except FileNotFoundError:
        return file_path.name


def get_now_ts() -> int:
    return int(time.time())


def days_to_seconds(days: int) -> int:
    return days * 24 * 60 * 60


def prune_expired_state_entries(state: dict, config: dict) -> tuple[set[str], set[str], bool]:
    now_ts = get_now_ts()
    skip_memory_days = config.get("skip_memory_days", 7)
    processed_memory_days = config.get("processed_memory_days", 30)

    skip_expiry = days_to_seconds(skip_memory_days)
    processed_expiry = days_to_seconds(processed_memory_days)

    changed = False

    valid_skipped = []
    skipped_keys = set()

    for item in state.get("skipped_archives", []):
        key = item.get("key")
        ts = item.get("timestamp", 0)

        if not key:
            changed = True
            continue

        if now_ts - ts <= skip_expiry:
            valid_skipped.append(item)
            skipped_keys.add(key)
        else:
            changed = True

    valid_processed = []
    processed_keys = set()

    for item in state.get("processed_archives", []):
        key = item.get("key")
        ts = item.get("timestamp", 0)

        if not key:
            changed = True
            continue

        if now_ts - ts <= processed_expiry:
            valid_processed.append(item)
            processed_keys.add(key)
        else:
            changed = True

    state["skipped_archives"] = valid_skipped
    state["processed_archives"] = valid_processed

    return skipped_keys, processed_keys, changed


def remember_archive_decision(state: dict, bucket: str, file_key: str) -> None:
    now_ts = get_now_ts()
    items = state.get(bucket, [])

    # replace existing entry if present
    filtered_items = [item for item in items if item.get("key") != file_key]
    filtered_items.append({
        "key": file_key,
        "timestamp": now_ts,
    })

    state[bucket] = filtered_items
    save_state(state)


def get_category_for_extension(extension: str, categories: dict, unknown_category: str) -> str:
    extension = extension.lower()

    for category_name, extensions in categories.items():
        if extension in [ext.lower() for ext in extensions]:
            return category_name

    return unknown_category


def is_ignored_file(file_name: str, config: dict) -> bool:
    name_lower = file_name.lower()

    for exact_name in config.get("ignored_exact_names", []):
        if name_lower == exact_name.lower():
            return True

    for prefix in config.get("ignored_prefixes", []):
        if name_lower.startswith(prefix.lower()):
            return True

    for ext in config.get("ignored_extensions", []):
        if name_lower.endswith(ext.lower()):
            return True

    return False


def is_archive(file_name: str, config: dict) -> bool:
    name_lower = file_name.lower()

    for ext in config.get("archive_extensions", []):
        if name_lower.endswith(ext.lower()):
            return True

    return False


def is_zip_file(file_path: Path) -> bool:
    return file_path.suffix.lower() == ".zip"


def is_valid_zip(file_path: Path) -> bool:
    try:
        with zipfile.ZipFile(file_path, "r") as zip_file:
            return zip_file.testzip() is None
    except Exception:
        return False


def ask_extract_archive(file_path: Path) -> bool:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    result = messagebox.askyesno(
        title="Artemis - Archive detected",
        message=f"Arhivă detectată:\n{file_path.name}\n\nVrei să o dezarhivezi în Downloads?",
        parent=root,
    )

    root.destroy()
    return result


def get_unique_extract_folder(base_folder: Path) -> Path:
    if not base_folder.exists():
        return base_folder

    counter = 1
    while True:
        candidate = base_folder.parent / f"{base_folder.name}_{counter}"
        if not candidate.exists():
            return candidate
        counter += 1


def extract_zip_in_place(file_path: Path) -> bool:
    if not is_valid_zip(file_path):
        log(f"Invalid or corrupted zip archive: {file_path.name}", level="ERROR")
        return False

    extract_folder = file_path.parent / file_path.stem
    extract_folder = get_unique_extract_folder(extract_folder)
    extract_folder.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(file_path, "r") as zip_file:
            zip_file.extractall(extract_folder)

        log(f"Extracted '{file_path.name}' -> '{extract_folder}'")
        return True
    except Exception as error:
        log(f"Failed to extract '{file_path.name}': {error}", level="ERROR")
        return False


def move_archive_to_sorted_archives(file_path: Path, config: dict) -> bool:
    destination_root = Path(config["destination_root"])
    archive_dir = destination_root / "Arhive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    existing_path = archive_dir / file_path.name
    is_duplicate_archive = False

    try:
        original_size = file_path.stat().st_size

        if existing_path.exists():
            existing_size = existing_path.stat().st_size

            if existing_size == original_size:
                is_duplicate_archive = True
                destination_path = get_duplicate_destination_path(archive_dir, file_path)

                log(f"Potential duplicate archive detected (same name + size): {file_path.name}")
            else:
                destination_path = get_safe_destination_path(archive_dir, file_path.name)
        else:
            destination_path = get_safe_destination_path(archive_dir, file_path.name)

        shutil.move(str(file_path), str(destination_path))
        log(f"Moved archive '{file_path.name}' -> '{destination_path}'")

        # orice arhivă mutată după extract poate fi cleanup candidate
        add_cleanup_item(
            str(destination_path),
            original_size,
            "duplicate_archive" if is_duplicate_archive else "archive"
        )

        return True

    except Exception as error:
        log(f"Failed to move archive '{file_path.name}': {error}", level="ERROR")
        return False

def is_file_locked(file_path: Path) -> bool:
    try:
        with open(file_path, "r+b"):
            return False
    except (PermissionError, OSError):
        return True


def is_file_stable(file_path: Path, wait_seconds: int) -> bool:
    if not file_path.exists() or not file_path.is_file():
        return False

    try:
        first_size = file_path.stat().st_size
        time.sleep(wait_seconds)
        second_size = file_path.stat().st_size
        return first_size == second_size
    except (FileNotFoundError, PermissionError, OSError):
        return False


def get_safe_destination_path(destination_dir: Path, original_name: str) -> Path:
    candidate = destination_dir / original_name

    if not candidate.exists():
        return candidate

    stem = Path(original_name).stem
    suffix = Path(original_name).suffix
    counter = 1

    while True:
        new_name = f"{stem}_{counter}{suffix}"
        candidate = destination_dir / new_name
        if not candidate.exists():
            return candidate
        counter += 1


def get_duplicate_destination_path(destination_dir: Path, file_path: Path) -> Path:
    stem = file_path.stem
    suffix = file_path.suffix

    if stem.endswith("_dup"):
        stem = stem[:-4]

    counter = 0

    while True:
        if counter == 0:
            candidate = destination_dir / f"{stem}_dup{suffix}"
        else:
            candidate = destination_dir / f"{stem}_dup_{counter}{suffix}"

        if not candidate.exists():
            return candidate

        counter += 1        

def move_file_to_category(
    file_path: Path,
    config: dict,
    skipped_archives: set[str],
    processed_archives: set[str],
    state: dict,
) -> bool:
    if not file_path.exists() or not file_path.is_file():
        return False

    file_name = file_path.name
    file_key = get_file_key(file_path)

    if is_ignored_file(file_name, config):
        log(f"Ignored file (pattern): {file_name}")
        return False

    if is_archive(file_name, config):
        if file_key in processed_archives:
            return False

        if file_key in skipped_archives:
            return False

        if is_zip_file(file_path):
            log(f"Zip archive detected: {file_name}")

            if ask_extract_archive(file_path):
                extracted = extract_zip_in_place(file_path)

                if extracted:
                    processed_archives.add(file_key)
                    remember_archive_decision(state, "processed_archives", file_key)

                    moved_archive = move_archive_to_sorted_archives(file_path, config)

                    if moved_archive:
                        log(f"Archive extracted and moved out of Downloads: {file_name}")
                    else:
                        log(
                            f"Archive extracted, but moving original archive failed: {file_name}",
                            level="WARNING",
                        )

                return False

            log(f"User skipped extraction for: {file_name}")
            skipped_archives.add(file_key)
            remember_archive_decision(state, "skipped_archives", file_key)
            return False

        log(f"Archive detected (non-zip, skipped for now): {file_name}")
        skipped_archives.add(file_key)
        remember_archive_decision(state, "skipped_archives", file_key)
        return False

    file_age = time.time() - file_path.stat().st_mtime
    if file_age < config.get("min_file_age_seconds", 5):
        log(f"File too new (waiting): {file_name}")
        return False

    if is_file_locked(file_path):
        log(f"Skipped (locked): {file_name}", level="WARNING")
        return False

    wait_seconds = config.get("stability_wait_seconds", 2)

    if not is_file_stable(file_path, wait_seconds):
        log(f"File not stable yet: {file_name}", level="WARNING")
        return False

    extension = file_path.suffix.lower()

    category = get_category_for_extension(
        extension=extension,
        categories=config["categories"],
        unknown_category=config["unknown_category"],
    )

    destination_root = Path(config["destination_root"])
    destination_dir = destination_root / category
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_path = get_safe_destination_path(destination_dir, file_name)

    existing_path = destination_dir / file_name
    is_potential_duplicate = False

    if existing_path.exists():
        try:
            existing_size = existing_path.stat().st_size
            new_size = file_path.stat().st_size

            if existing_size == new_size:
                is_potential_duplicate = True
                destination_path = get_duplicate_destination_path(destination_dir, file_path)

                log(f"Potential duplicate detected (same name + size): {file_name}")
            else:
                destination_path = get_safe_destination_path(destination_dir, file_name)

        except Exception as error:
            log(f"Duplicate check failed for '{file_name}': {error}", level="WARNING")
            destination_path = get_safe_destination_path(destination_dir, file_name)
    else:
        destination_path = get_safe_destination_path(destination_dir, file_name)

    try:
        shutil.move(str(file_path), str(destination_path))
        log(f"Moved '{file_name}' -> '{destination_path}'")

        if is_potential_duplicate:
            add_cleanup_item(
                str(destination_path),
                destination_path.stat().st_size,
                "duplicate"
            )

       
        return True    
    
    except Exception as error:
        log(f"Failed to move '{file_name}': {error}", level="ERROR")
        return False


class DownloadsHandler(FileSystemEventHandler):
    def __init__(self, pending_files: set[str]):
        self.pending_files = pending_files

    def on_created(self, event):
        if event.is_directory:
            return
        self.pending_files.add(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.pending_files.add(event.src_path)

def acquire_lock() -> bool:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    if LOCK_FILE.exists():
        try:
            existing_pid = int(PID_FILE.read_text().strip())

            import psutil

            if psutil.pid_exists(existing_pid):
                log(
                    "Downloads sorter is already running. Exiting duplicate instance.",
                    level="WARNING",
                )
                return False

            log("Stale lock detected. Cleaning up runtime files.", level="WARNING")

        except Exception:
            log("Invalid lock/PID state detected. Cleaning up runtime files.", level="WARNING")

        for file_path in [LOCK_FILE, PID_FILE, STOP_FILE]:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as error:
                log(f"Failed to clean stale runtime file {file_path}: {error}", level="ERROR")
                return False

    try:
        pid = os.getpid()

        LOCK_FILE.write_text(f"{get_now_ts()}|{pid}", encoding="utf-8")
        PID_FILE.write_text(str(pid), encoding="utf-8")

        if STOP_FILE.exists():
            STOP_FILE.unlink()

        log(f"Lock acquired. PID: {pid}")
        return True

    except Exception as error:
        log(f"Failed to create runtime files: {error}", level="ERROR")
        return False


def release_lock() -> None:
    for file_path in [LOCK_FILE, PID_FILE, STOP_FILE]:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as error:
            log(f"Failed to remove runtime file {file_path}: {error}", level="ERROR")

def get_duplicate_destination_path(destination_dir: Path, file_path: Path) -> Path:
    stem = file_path.stem
    suffix = file_path.suffix

    if stem.endswith("_dup"):
        stem = stem[:-4]

    counter = 0

    while True:
        if counter == 0:
            candidate = destination_dir / f"{stem}_dup{suffix}"
        else:
            candidate = destination_dir / f"{stem}_dup_{counter}{suffix}"

        if not candidate.exists():
            return candidate

        counter += 1
        
def main():
    if not acquire_lock():
        return

    observer = None

    try:
        config = load_config()
        state = load_state()

        skipped_archives, processed_archives, state_changed = prune_expired_state_entries(state, config)
        if state_changed:
            save_state(state)

        watch_folder = Path(config["watch_folder"])
        if not watch_folder.exists():
            raise FileNotFoundError(f"Watch folder does not exist: {watch_folder}")

        pending_files: set[str] = set()

        process_existing_on_startup = config.get("process_existing_on_startup", True)
        if process_existing_on_startup:
            for item in watch_folder.iterdir():
                if item.is_file():
                    pending_files.add(str(item))

        event_handler = DownloadsHandler(pending_files)
        observer = Observer()
        observer.schedule(event_handler, str(watch_folder), recursive=False)
        observer.start()

        log(f"Watching folder: {watch_folder}")
        log(f"Process existing on startup: {process_existing_on_startup}")
        write_activity_state("idle", "Watching Downloads")

        last_cleanup_run = 0
        CLEANUP_INTERVAL = 600  # 10 minute

        while True:
            now = time.time()

            if now - last_cleanup_run > CLEANUP_INTERVAL:
                clean_invalid_items()
                last_cleanup_run = now

            if STOP_FILE.exists():
                log("Stop signal detected. Shutting down sorter.")
                write_activity_state("idle", "Stopped")
                break

            if not pending_files:
                write_activity_state("idle", "Watching Downloads")

            for file_str in list(pending_files):
                file_path = Path(file_str)

                if not file_path.exists():
                    pending_files.discard(file_str)
                    continue

                write_activity_state("active", f"Checking {file_path.name}")

                moved = move_file_to_category(
                    file_path,
                    config,
                    skipped_archives,
                    processed_archives,
                    state,
                )

                if moved:
                    write_activity_state("idle", "Watching Downloads")
                    pending_files.discard(file_str)
                    continue

                if is_ignored_file(file_path.name, config):
                    write_activity_state("idle", "Watching Downloads")
                    pending_files.discard(file_str)
                    continue

                file_key = get_file_key(file_path)

                if is_archive(file_path.name, config):
                    if not is_zip_file(file_path):
                        write_activity_state("idle", "Watching Downloads")
                        pending_files.discard(file_str)
                        continue

                    if file_key in skipped_archives or file_key in processed_archives:
                        write_activity_state("idle", "Watching Downloads")
                        pending_files.discard(file_str)
                        continue

                write_activity_state("idle", "Watching Downloads")

            time.sleep(2)

    except KeyboardInterrupt:
        log("Stopping downloads auto sorter.")
        write_activity_state("idle", "Stopped by keyboard interrupt")

    except Exception as error:
        log(f"Downloads sorter crashed: {error}", level="ERROR")
        write_activity_state("error", str(error))

    finally:
        if observer is not None:
            observer.stop()
            observer.join()

        release_lock()
        
if __name__ == "__main__":
    main()        