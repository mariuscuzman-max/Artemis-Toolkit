from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_FILE = ROOT / "artemis_context_bundle.txt"

INCLUDE_EXTENSIONS = {".py", ".json", ".ahk", ".md"}
EXCLUDE_FOLDERS = {".venv", "__pycache__", ".git", "logs", "runtime", "node_modules"}
EXCLUDE_FILES = {
    "artemis_context_bundle.txt",
    "make_context_bundle.py",
    "tree.txt",
    "artemis_debug_bundle.txt",
    "artemis_review_bundle.txt",
    "luna_review_snippet.txt",
}

# Priority for sorting: Core files first, then features, then utils/others
PRIORITY_MAP = {
    "core": 1,
    "main": 1,
    "features": 2,
    "utils": 3,
    "config": 4
}

def get_priority(path: Path) -> int:
    parts = path.parts
    for part in parts:
        if part.lower() in PRIORITY_MAP:
            return PRIORITY_MAP[part.lower()]
    return 5  # Default lowest priority

def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_FOLDERS for part in path.parts):
        return True
    if path.name in EXCLUDE_FILES or " - Copy" in path.name:
        return True
    return False

def estimate_tokens(text: str) -> int:
    return len(text) // 4

with OUTPUT_FILE.open("w", encoding="utf-8") as out:
    out.write("# ARTEMIS TOOLKIT CONTEXT BUNDLE\n\n")
    out.write("## PROJECT DESCRIPTION\n\n")
    out.write("Artemis Toolkit: Windows automation using Python, JSON, and AHK.\n\n")

    # 1. Generate File Tree with priority sorting
    out.write("## FILE TREE\n\n")
    all_paths = sorted([p for p in ROOT.rglob("*") if not should_skip(p)], key=get_priority)
    for path in all_paths:
        rel = path.relative_to(ROOT)
        out.write(f"{rel}/\n" if path.is_dir() else f"{rel}\n")

    # 2. Generate File Contents
    out.write("\n\n## FILE CONTENTS\n\n")
    # Re-sort files for content injection based on priority
    content_files = sorted(
        [p for p in all_paths if p.is_file() and p.suffix.lower() in INCLUDE_EXTENSIONS],
        key=get_priority
    )

    for path in content_files:
        rel_path = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")

        tokens = estimate_tokens(text)
        out.write(f"\n\n--- FILE: {rel_path} ({tokens} tokens) ---\n\n")

        # Only truncate non-python files to prevent breaking logic
        max_chars = 15000
        if path.suffix.lower() != ".py" and len(text) > max_chars:
            out.write(text[:max_chars])
            out.write("\n\n[FILE TRUNCATED TO SAVE SPACE]")
        else:
            out.write(text)

print(f"Done! Bundle created at: {OUTPUT_FILE}")