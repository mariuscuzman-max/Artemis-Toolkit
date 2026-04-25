from pathlib import Path

# This means: use the folder where this script is located
ROOT = Path(__file__).parent

# This is the file we will create for the AI
OUTPUT_FILE = ROOT / "artemis_context_bundle.txt"

# File types we want to include
INCLUDE_EXTENSIONS = {
    ".py",
    ".json",
    ".ahk",
    ".md",
    ".txt",
}

# Folders we do NOT want to include
EXCLUDE_FOLDERS = {
    ".venv",
    "__pycache__",
    ".git",
    "logs",
    "node_modules",
}

EXCLUDE_FILES = {
    "artemis_context_bundle.txt",
    "make_context_bundle.py",
}

def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_FOLDERS:
            return True

    if path.name in EXCLUDE_FILES:
        return True

    if " - Copy" in path.name:
        return True

    return False


with OUTPUT_FILE.open("w", encoding="utf-8") as out:
    out.write("# ARTEMIS TOOLKIT CONTEXT BUNDLE\n\n")

    out.write("## PROJECT DESCRIPTION\n\n")
    out.write(
        "Artemis Toolkit is a Windows automation project. "
        "It launches apps/scripts based on modes like work, gaming, and utilities. "
        "It uses Python, JSON config files, and AutoHotkey scripts.\n\n"
    )

    out.write("## FILE TREE\n\n")

    for path in sorted(ROOT.rglob("*")):
        if should_skip(path):
            continue

        relative_path = path.relative_to(ROOT)

        if path.is_dir():
            out.write(f"{relative_path}/\n")
        else:
            out.write(f"{relative_path}\n")

    out.write("\n\n## FILE CONTENTS\n\n")

    for path in sorted(ROOT.rglob("*")):
        if should_skip(path):
            continue

        if path.is_file() and path.suffix.lower() in INCLUDE_EXTENSIONS:
            relative_path = path.relative_to(ROOT)

            out.write(f"\n\n--- FILE: {relative_path} ---\n\n")

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="latin-1")

            # Avoid feeding monster files
            max_chars = 12000

            if len(text) > max_chars:
                out.write(text[:max_chars])
                out.write("\n\n[FILE TRUNCATED BECAUSE IT WAS TOO LARGE]\n")
            else:
                out.write(text)

print(f"Done. Created: {OUTPUT_FILE}")