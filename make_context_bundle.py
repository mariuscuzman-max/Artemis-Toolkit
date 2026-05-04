import os
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT_FILE = ROOT / "artemis_master_bundle.txt"

# Files that contain your rules (adjust names if needed)
VISION_FILE = ROOT / "vision.md"
ROADMAP_FILE = ROOT / "roadmap.md"

INCLUDE_EXTENSIONS = {".py", ".json", ".ahk", ".md"}
EXCLUDE_FOLDERS = {".venv", "__pycache__", ".git", "logs", "runtime", "node_modules"}
EXCLUDE_FILES = {
    "artemis_master_bundle.txt",
    "make_context_bundle.py",
    "vision.md",   # Excluded from the code loop because we inject them at the top
    "roadmap.md"
}

def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_FOLDERS for part in path.parts):
        return True
    if path.name in EXCLUDE_FILES or " - Copy" in path.name:
        return True
    return False

def generate_tree(dir_path: Path, prefix: str = "") -> str:
    """Generates a clean visual file tree to prevent AI hallucinations."""
    tree_str = ""
    paths = sorted([p for p in dir_path.iterdir() if not should_skip(p)], 
                   key=lambda p: (not p.is_dir(), p.name.lower()))
    
    for i, path in enumerate(paths):
        is_last = i == len(paths) - 1
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{path.name}\n"
        
        if path.is_dir():
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(path, prefix + extension)
    return tree_str

def main():
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        # --- 1. INJECT VISION & ROADMAP FIRST ---
        out.write("# ==========================================\n")
        out.write("# 1. ARTEMIS VISION & UX GUIDELINES\n")
        out.write("# ==========================================\n\n")
        if VISION_FILE.exists():
            out.write(VISION_FILE.read_text(encoding="utf-8") + "\n\n")
        else:
            out.write("[Vision document not found]\n\n")

        out.write("# ==========================================\n")
        out.write("# 2. ARTEMIS MASTER ROADMAP\n")
        out.write("# ==========================================\n\n")
        if ROADMAP_FILE.exists():
            out.write(ROADMAP_FILE.read_text(encoding="utf-8") + "\n\n")
        else:
            out.write("[Roadmap document not found]\n\n")

        # --- 2. FILE TREE (The Map) ---
        out.write("# ==========================================\n")
        out.write("# 3. PROJECT DIRECTORY STRUCTURE\n")
        out.write("# (Crucial: Do not assume files exist outside this tree)\n")
        out.write("# ==========================================\n\n")
        out.write(f"{ROOT.name}/\n")
        out.write(generate_tree(ROOT))
        out.write("\n\n")

        # --- 3. FULL SOURCE CODE ---
        out.write("# ==========================================\n")
        out.write("# 4. FULL SOURCE CODE\n")
        out.write("# ==========================================\n")
        
        all_paths = sorted([p for p in ROOT.rglob("*") if p.is_file() and not should_skip(p)])
        content_files = [p for p in all_paths if p.suffix.lower() in INCLUDE_EXTENSIONS]

        for path in content_files:
            rel_path = path.relative_to(ROOT)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="latin-1")

            out.write(f"\n\n{'='*60}\n")
            out.write(f"--- FILE: {rel_path} ---\n")
            out.write(f"{'='*60}\n\n")
            
            # Truncate large non-code files, keep all python/json
            if path.suffix.lower() not in [".py", ".json"] and len(text) > 15000:
                out.write(text[:15000] + "\n\n[TRUNCATED TO SAVE SPACE]")
            else:
                out.write(text)

    print(f"Master bundle created successfully at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()