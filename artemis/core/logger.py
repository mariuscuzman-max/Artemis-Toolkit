from datetime import datetime

from artemis.core.path_utils import get_user_logs_dir

LOG_FILE = get_user_logs_dir() / "artemis.log"


def log(message: str, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}"

    print(line)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line + "\n")
