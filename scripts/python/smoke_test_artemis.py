import copy
import os
import sys
import tempfile
import types
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))
TEST_APPDATA_DIR = tempfile.TemporaryDirectory(prefix="artemis_appdata_")
os.environ["ARTEMIS_APPDATA_DIR"] = TEST_APPDATA_DIR.name


def install_watchdog_import_stub_if_missing() -> None:
    try:
        import watchdog.events  # noqa: F401
        import watchdog.observers  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    watchdog_module = types.ModuleType("watchdog")
    events_module = types.ModuleType("watchdog.events")
    observers_module = types.ModuleType("watchdog.observers")

    class FileSystemEventHandler:
        pass

    class Observer:
        pass

    events_module.FileSystemEventHandler = FileSystemEventHandler
    observers_module.Observer = Observer
    watchdog_module.events = events_module
    watchdog_module.observers = observers_module

    sys.modules.setdefault("watchdog", watchdog_module)
    sys.modules.setdefault("watchdog.events", events_module)
    sys.modules.setdefault("watchdog.observers", observers_module)


install_watchdog_import_stub_if_missing()

from artemis.core import cleanup_tracker, recent_activity
from artemis.core.rules_engine import find_first_matching_user_rule
from scripts.python.downloads_auto_sorter import (
    CONFIG_PATH,
    get_category_for_extension,
    is_archive,
    is_zip_file,
    load_config,
    move_file_to_category,
)


def print_result(name: str, passed: bool, detail: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


def require(condition: bool, name: str, detail: str = "") -> None:
    print_result(name, condition, detail)

    if not condition:
        raise AssertionError(name)


def make_test_config(base_config: dict, fake_downloads: Path, sorted_root: Path) -> dict:
    config = copy.deepcopy(base_config)
    config["watch_folder"] = str(fake_downloads)
    config["destination_root"] = str(sorted_root)
    config["process_existing_on_startup"] = False
    config["stability_wait_seconds"] = 0
    config["min_file_age_seconds"] = 0
    return config


def create_sample_files(fake_downloads: Path) -> dict[str, Path]:
    samples = {
        "pdf": fake_downloads / "test.pdf",
        "exe": fake_downloads / "test.exe",
        "txt": fake_downloads / "test.txt",
        "zip": fake_downloads / "test.zip",
        "sameday_pdf": fake_downloads / "invoice_sameday.pdf",
    }

    samples["pdf"].write_text("fake pdf content", encoding="utf-8")
    samples["exe"].write_text("fake exe content", encoding="utf-8")
    samples["txt"].write_text("fake text content", encoding="utf-8")
    samples["sameday_pdf"].write_text("fake sameday pdf content", encoding="utf-8")

    with zipfile.ZipFile(samples["zip"], "w") as zip_file:
        zip_file.writestr("inside.txt", "hello from zip")

    return samples


def main() -> int:
    print("Artemis backend smoke test")
    print(f"Config: {CONFIG_PATH}")

    try:
        base_config = load_config()
        require(isinstance(base_config, dict), "Load downloads sorter config")
    except Exception as error:
        print_result("Load downloads sorter config", False, str(error))
        return 1

    original_cleanup_file = cleanup_tracker.CLEANUP_FILE
    original_recent_activity_file = recent_activity.RECENT_ACTIVITY_FILE

    try:
        with tempfile.TemporaryDirectory(prefix="artemis_smoke_") as temp_dir:
            temp_root = Path(temp_dir)
            fake_downloads = temp_root / "Downloads"
            sorted_root = fake_downloads / "Sorted"
            runtime_dir = temp_root / "runtime"

            fake_downloads.mkdir(parents=True, exist_ok=True)
            runtime_dir.mkdir(parents=True, exist_ok=True)

            cleanup_tracker.CLEANUP_FILE = runtime_dir / "cleanup_queue.json"
            recent_activity.RECENT_ACTIVITY_FILE = runtime_dir / "recent_activity.json"

            config = make_test_config(base_config, fake_downloads, sorted_root)
            samples = create_sample_files(fake_downloads)

            require(fake_downloads.exists(), "Create temporary fake Downloads folder")
            require(samples["pdf"].exists(), "Create sample PDF")
            require(samples["exe"].exists(), "Create sample EXE")
            require(samples["txt"].exists(), "Create sample TXT")
            require(samples["zip"].exists(), "Create sample ZIP")
            require(samples["sameday_pdf"].exists(), "Create sample name-match PDF")

            require(
                get_category_for_extension(".pdf", config["categories"], config["unknown_category"]) == "Documente",
                "Resolve PDF category",
            )
            require(is_archive(samples["zip"].name, config), "Detect ZIP as archive")
            require(is_zip_file(samples["zip"]), "Detect ZIP file type")

            skipped_archives: set[str] = set()
            processed_archives: set[str] = set()
            state = {"skipped_archives": [], "processed_archives": []}

            sameday_destination = sorted_root / "Sameday"
            sameday_destination.mkdir(parents=True, exist_ok=True)
            config["user_rules"] = {
                "enabled": True,
                "rules": [
                    {
                        "id": "smoke_sameday_pdf",
                        "name": "Move Sameday PDFs",
                        "enabled": True,
                        "conditions": [
                            {
                                "type": "extension",
                                "value": ".pdf",
                            },
                            {
                                "type": "name_contains",
                                "value": "sameday",
                            },
                        ],
                        "action": {
                            "type": "move_to",
                            "destination": str(sameday_destination),
                        },
                    }
                ],
            }

            require(
                find_first_matching_user_rule(samples["sameday_pdf"], config) is not None,
                "Match multi-condition AND user rule",
            )
            require(
                find_first_matching_user_rule(samples["pdf"], config) is None,
                "Do not match AND rule when filename text is missing",
            )

            moved = move_file_to_category(
                samples["sameday_pdf"],
                config,
                skipped_archives,
                processed_archives,
                state,
            )
            require(moved is True, "Move PDF by multi-condition user rule")
            require(
                (sameday_destination / "invoice_sameday.pdf").exists(),
                "Verify multi-condition rule destination",
            )

            for key in ["pdf", "exe", "txt"]:
                moved = move_file_to_category(
                    samples[key],
                    config,
                    skipped_archives,
                    processed_archives,
                    state,
                )
                require(moved is True, f"Move {samples[key].name}")

            require(
                (sorted_root / "Documente" / "test.pdf").exists(),
                "Verify PDF moved to Sorted/Documente",
            )
            require(
                (sorted_root / "Installers" / "test.exe").exists(),
                "Verify EXE moved to Sorted/Installers",
            )
            require(
                (sorted_root / "Documente" / "test.txt").exists(),
                "Verify TXT moved to Sorted/Documente",
            )

            missing_path = temp_root / "missing-file.tmp"
            cleanup_tracker.add_cleanup_item(str(missing_path), 123, "smoke_invalid")
            require(
                cleanup_tracker.get_cleanup_stats()[0] == 1,
                "Create temp cleanup queue item",
            )

            cleanup_tracker.clean_invalid_items()
            require(
                cleanup_tracker.get_cleanup_stats()[0] == 0,
                "Clean invalid cleanup queue item",
            )

            recent_activity.record_recent_activity(
                action="Smoke test event",
                source_path=str(sorted_root / "Documente" / "test.pdf"),
                detail="backend smoke test",
            )
            activity_items = recent_activity.get_recent_activity(limit=1)
            require(
                len(activity_items) == 1
                and activity_items[0].get("action") == "Smoke test event",
                "Record and read recent activity",
            )

        print("[PASS] Smoke test completed without touching real Downloads files")
        return 0

    except Exception as error:
        print_result("Smoke test failed", False, str(error))
        return 1

    finally:
        cleanup_tracker.CLEANUP_FILE = original_cleanup_file
        recent_activity.RECENT_ACTIVITY_FILE = original_recent_activity_file
        TEST_APPDATA_DIR.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
