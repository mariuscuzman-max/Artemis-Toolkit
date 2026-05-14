# Artemis Toolkit

Artemis Toolkit is a local Windows tray utility that keeps your Downloads folder clean.

Core idea:

> Turn it on once, your Downloads folder sorts itself by extension into folders, and you get nudged to delete stuff you do not use.

Artemis is designed to be quiet, safe, and local. It does not use cloud services, accounts, or background data collection.

## Current status

Tester build moving toward a packaged Windows release.

The app currently supports:

- automatic Downloads sorting
- default extension-based sorting
- custom rules from the tray UI
- extension and filename-based AND rules
- safe duplicate renaming
- cleanup queue with manual delete/postpone actions
- recent activity history
- tray UI with sorter status
- duplicate tray instance prevention
- portable Windows Downloads paths
- first-run user config/runtime/logs under `%LOCALAPPDATA%\Artemis Toolkit`

## Safety rule

Artemis never deletes files automatically.

Cleanup actions always require user confirmation.

## Current limitations

- Windows-only for now
- no installer yet
- archive handling is conservative
- UI is functional but still being polished

## How to run

Requires Python and dependencies from `requirements.txt`.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python artemis_app.py
```

The repository `config/downloads_sorter.json` is the default template. The live user config is created on first run at:

```text
%LOCALAPPDATA%\Artemis Toolkit\config\downloads_sorter.json
```

## Tray icon visibility

Windows may place Artemis in the hidden tray icons menu after launch. To keep Artemis visible, open the hidden icons arrow in the taskbar and drag the Artemis icon next to your network and volume icons. Windows controls this as a user preference, so Artemis does not force the icon into the visible tray area.
