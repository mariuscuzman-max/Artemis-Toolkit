import ast
from pathlib import Path

FILE = Path("scripts/python/downloads_auto_sorter.py")
OUT = Path("luna_review_snippet.txt")

TARGET_FUNCTIONS = {
    "move_file_to_category",
    "is_archive",
    "is_zip_file",
    "is_ignored_file",
    "get_file_key",
    "remember_archive_decision",
}


source = FILE.read_text(encoding="utf-8")
lines = source.splitlines(keepends=True)
tree = ast.parse(source)

blocks = []

for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in TARGET_FUNCTIONS:
        start = node.lineno - 1
        end = node.end_lineno
        blocks.append("".join(lines[start:end]))

# Extract main() separately, because the loop is inside it.
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "main":
        start = node.lineno - 1
        end = node.end_lineno
        blocks.append("".join(lines[start:end]))

OUT.write_text("\n\n\n".join(blocks), encoding="utf-8")

print(f"Saved review snippet to: {OUT}")