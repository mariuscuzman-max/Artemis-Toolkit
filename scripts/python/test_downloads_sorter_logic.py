import tempfile
import time
import zipfile
from pathlib import Path

from downloads_auto_sorter import (
    is_ignored_file,
    is_archive,
    is_zip_file,
    get_safe_destination_path,
    prune_expired_state_entries,
    is_valid_zip,
)


def test_ignore_rules():
    config = {
        "ignored_exact_names": ["desktop.ini"],
        "ignored_prefixes": ["~$", ".~"],
        "ignored_extensions": [".tmp", ".crdownload"],
    }

    assert is_ignored_file("desktop.ini", config)
    assert is_ignored_file("~$document.docx", config)
    assert is_ignored_file("file.tmp", config)
    assert not is_ignored_file("photo.png", config)


def test_archive_detection():
    config = {
        "archive_extensions": [".zip", ".rar", ".7z"]
    }

    assert is_archive("test.zip", config)
    assert is_archive("backup.rar", config)
    assert not is_archive("image.png", config)


def test_zip_detection():
    assert is_zip_file(Path("test.zip"))
    assert not is_zip_file(Path("test.rar"))


def test_safe_destination_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)
        existing = folder / "file.txt"
        existing.write_text("already here", encoding="utf-8")

        safe_path = get_safe_destination_path(folder, "file.txt")

        assert safe_path.name == "file_1.txt"


def test_state_expiry():
    now = int(time.time())

    state = {
        "skipped_archives": [
            {"key": "old.zip_100", "timestamp": now - (10 * 24 * 60 * 60)},
            {"key": "new.zip_100", "timestamp": now},
        ],
        "processed_archives": []
    }

    config = {
        "skip_memory_days": 7,
        "processed_memory_days": 30,
    }

    skipped, processed, changed = prune_expired_state_entries(state, config)

    assert "old.zip_100" not in skipped
    assert "new.zip_100" in skipped
    assert changed is True


def test_valid_and_corrupted_zip():
    with tempfile.TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)

        good_zip = folder / "good.zip"
        with zipfile.ZipFile(good_zip, "w") as z:
            z.writestr("hello.txt", "hello")

        bad_zip = folder / "bad.zip"
        bad_zip.write_text("not a real zip", encoding="utf-8")

        assert is_valid_zip(good_zip)
        assert not is_valid_zip(bad_zip)


def run_all_tests():
    test_ignore_rules()
    test_archive_detection()
    test_zip_detection()
    test_safe_destination_path()
    test_state_expiry()
    test_valid_and_corrupted_zip()

    print("All downloads sorter logic tests passed.")


if __name__ == "__main__":
    run_all_tests()