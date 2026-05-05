# Artemis Toolkit

Artemis Toolkit is a local Windows tray utility that keeps your Downloads folder clean.

Core idea:

> Turn it on once, your Downloads folder sorts itself by extension into folders, and you get nudged to delete stuff you do not use.

Artemis is designed to be quiet, safe, and local. It does not use cloud services, accounts, or background data collection.

## Current status

Early development / tester build.

The app currently supports:

- automatic Downloads sorting
- default extension-based sorting
- custom user rules from config
- safe duplicate renaming
- cleanup queue with manual delete/postpone actions
- recent activity history
- tray UI with sorter status
- duplicate tray instance prevention

## Safety rule

Artemis never deletes files automatically.

Cleanup actions always require user confirmation.

## Current limitations

- Windows-only for now
- no installer yet
- custom rules are still being built
- some settings are still config-based
- UI is functional but not final

## How to run

Requires Python and dependencies from `requirements.txt`.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python artemis\ui\tray.py