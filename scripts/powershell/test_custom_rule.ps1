$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$script = @'
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

repo_root = Path.cwd()
sys.path.insert(0, str(repo_root))
test_appdata_dir = tempfile.TemporaryDirectory(prefix="artemis_appdata_")
os.environ["ARTEMIS_APPDATA_DIR"] = test_appdata_dir.name

from artemis.core import cleanup_tracker, recent_activity
from artemis.core.rules_engine import find_first_matching_user_rule
from scripts.python.downloads_auto_sorter import (
    load_config,
    move_file_to_category,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

    print(f"[PASS] {message}")


base_config = load_config()

original_cleanup_file = cleanup_tracker.CLEANUP_FILE
original_recent_activity_file = recent_activity.RECENT_ACTIVITY_FILE

try:
    with tempfile.TemporaryDirectory(prefix="artemis_rule_test_") as temp_dir:
        temp_root = Path(temp_dir)
        fake_downloads = temp_root / "Downloads"
        sorted_root = fake_downloads / "Sorted"
        rule_destination = sorted_root / "Apples"
        runtime_dir = temp_root / "runtime"

        fake_downloads.mkdir(parents=True, exist_ok=True)
        rule_destination.mkdir(parents=True, exist_ok=True)
        runtime_dir.mkdir(parents=True, exist_ok=True)

        cleanup_tracker.CLEANUP_FILE = runtime_dir / "cleanup_queue.json"
        recent_activity.RECENT_ACTIVITY_FILE = runtime_dir / "recent_activity.json"

        config = copy.deepcopy(base_config)
        config["watch_folder"] = str(fake_downloads)
        config["destination_root"] = str(sorted_root)
        config["process_existing_on_startup"] = False
        config["stability_wait_seconds"] = 0
        config["min_file_age_seconds"] = 0
        config["user_rules"] = {
            "enabled": True,
            "rules": [
                {
                    "id": "test_pdf_apples_rule",
                    "name": "Move apple PDFs",
                    "enabled": True,
                    "conditions": [
                        {
                            "type": "extension",
                            "value": ".pdf",
                        },
                        {
                            "type": "name_contains",
                            "value": "apples",
                        },
                    ],
                    "action": {
                        "type": "move_to",
                        "destination": str(rule_destination),
                    },
                }
            ],
        }

        matching_file = fake_downloads / "fresh_apples_invoice.pdf"
        non_matching_file = fake_downloads / "fresh_oranges_invoice.pdf"

        matching_file.write_text("custom rule should move this", encoding="utf-8")
        non_matching_file.write_text("default sorter should move this", encoding="utf-8")

        require(
            find_first_matching_user_rule(matching_file, config) is not None,
            "Rule matches .pdf files whose name contains apples",
        )
        require(
            find_first_matching_user_rule(non_matching_file, config) is None,
            "Rule does not match .pdf files without apples in the name",
        )

        skipped_archives: set[str] = set()
        processed_archives: set[str] = set()
        state = {"skipped_archives": [], "processed_archives": []}

        require(
            move_file_to_category(
                matching_file,
                config,
                skipped_archives,
                processed_archives,
                state,
            ) is True,
            "Sorter moves matching file by custom rule",
        )

        require(
            (rule_destination / "fresh_apples_invoice.pdf").exists(),
            "Matching file lands in the custom Apples destination",
        )

        require(
            move_file_to_category(
                non_matching_file,
                config,
                skipped_archives,
                processed_archives,
                state,
            ) is True,
            "Sorter falls back to default sorting for non-matching file",
        )

        require(
            (sorted_root / "Documents" / "fresh_oranges_invoice.pdf").exists(),
            "Non-matching PDF lands in the default Documents destination",
        )

        print("")
        print("Custom rule under test:")
        print(json.dumps(config["user_rules"]["rules"][0], indent=2))

finally:
    cleanup_tracker.CLEANUP_FILE = original_cleanup_file
    recent_activity.RECENT_ACTIVITY_FILE = original_recent_activity_file
    test_appdata_dir.cleanup()
'@

Push-Location $repoRoot
try {
    $script | & $python -
}
finally {
    Pop-Location
}
