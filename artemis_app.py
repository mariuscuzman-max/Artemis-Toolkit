import sys


def main() -> None:
    if "--sorter" in sys.argv:
        from scripts.python.downloads_auto_sorter import main as run_sorter

        run_sorter()
        return

    from artemis.ui.tray import run_tray_app

    run_tray_app()


if __name__ == "__main__":
    main()
