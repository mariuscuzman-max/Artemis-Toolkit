from pathlib import Path
from datetime import datetime
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "PROJECT_AUDIT.txt"

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "runtime", "logs"}


def run_cmd(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return result.stderr.strip() or "[command failed]"
        return result.stdout.strip() or "[no output]"
    except Exception as error:
        return f"[error running command: {error}]"


def generate_file_tree() -> str:
    lines = []

    for path in sorted(ROOT.rglob("*")):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        relative = path.relative_to(ROOT)

        if path.is_file() and path.suffix.lower() in {".py", ".json", ".md", ".txt"}:
            lines.append(str(relative))

    return "\n".join(lines) if lines else "[no files found]"


def main():
    parts = []

    parts.append(f"# PROJECT AUDIT")
    parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    parts.append("")

    parts.append("## Git branch")
    parts.append(run_cmd(["git", "branch", "--show-current"]))
    parts.append("")

    parts.append("## Last commit")
    parts.append(run_cmd(["git", "log", "-1", "--oneline"]))
    parts.append("")

    parts.append("## Git status")
    parts.append(run_cmd(["git", "status", "--short"]))
    parts.append("")

    parts.append("## Git diff stat")
    parts.append(run_cmd(["git", "diff", "--stat"]))
    parts.append("")

    parts.append("## File tree snapshot")
    parts.append(generate_file_tree())
    parts.append("")

    parts.append("## Tests")
    parts.append("Tests not auto-run by this script. Paste manual test results separately.")
    parts.append("")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Audit written to: {OUT}")


if __name__ == "__main__":
    main()
    