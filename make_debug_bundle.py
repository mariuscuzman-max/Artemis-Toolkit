from pathlib import Path

for p in Path(".").rglob("*"):
    if any(x in p.parts for x in [".venv", "__pycache__", ".git"]):
        continue
    print(p)
    