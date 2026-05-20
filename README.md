# Artemis Toolkit

Artemis Toolkit is a local Windows tray utility that keeps your Downloads folder clean.

Core idea:

> Turn it on once, your Downloads folder sorts itself by extension into folders, and you get nudged to delete stuff you do not use.

Artemis is designed to be quiet, safe, and local. It does not use cloud services, accounts, or background data collection.

## Preview

### Dashboard

The Status page shows whether Artemis is monitoring Downloads and keeps a recent activity log of files it has moved.

![Artemis dashboard showing active monitoring and recent file activity](Screenshot%202026-05-20%20150639.png)

### Customize rules

The Customize page lets you add extension and filename-based sorting rules, choose the action, and set a destination folder.

![Artemis customize page for creating sorting rules](Screenshot%202026-05-19%20175552.png)

### Sorting in action

This demo shows a file disappearing from Downloads as Artemis sorts it, while the dashboard updates with the activity.

![Artemis sorting a file while the dashboard records the move](Artemis%20gif.gif)

## Current status

Packaged Windows tester build.

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
- packaged EXE and installer exist for internal alpha testing
- archive handling is conservative
- UI is functional but still being polished
- no cloud sync, accounts, or cross-device behavior
- no content-based document scanning yet
- custom rules support extension/name matching with AND logic, but not OR/nested groups

## Install

Download and run the current installer:

```text
dist\installer\ArtemisToolkitSetup-v0.6.1.exe
```

The Windows installer creates a Task Scheduler entry named `Artemis Toolkit` so Artemis starts when the user logs into Windows. When first-run setup is complete, the tray app starts the sorter automatically.

The Settings page includes a `Run setup wizard` button so onboarding can be reviewed or repeated without resetting Downloads data.

The tray menu `Quit Artemis` action shuts down both the tray UI and the background sorter.

## Packaged build details

The PyInstaller onedir build is created at:

```text
dist\ArtemisToolkit\ArtemisToolkit.exe
```

This build uses:

- app icon from `icons\app.ico`
- Windows version metadata from `packaging\windows_version_info.txt`
- bundled default config template from `config`
- bundled tray/app icons from `icons`

## Run from source

For development, Artemis can also be run directly with Python and dependencies from `requirements.txt`.

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

## Reset behavior

Artemis stores live user data here:

```text
%LOCALAPPDATA%\Artemis Toolkit
```

That folder may contain config, logs, runtime state, cleanup queue data, and recent activity history.

To fully reset Artemis to a first-run state, close Artemis completely, then remove:

```text
%LOCALAPPDATA%\Artemis Toolkit
```

This does not delete files from Downloads or from any folders Artemis previously sorted files into.

## Uninstall behavior

The installer should remove installed application files only.

The installer should also remove the `Artemis Toolkit` Task Scheduler startup entry.

Each installer run writes a small reinstall marker into the app install folder. On next launch, Artemis compares that marker with the live user config and resets the setup wizard flag in:

```text
%LOCALAPPDATA%\Artemis Toolkit\config\downloads_sorter.json
```

This means a later reinstall shows the first-run wizard again while still preserving the rest of the user config unless the user changes it in setup.

Uninstall must not silently delete:

- the user's Downloads files
- sorted destination folders
- files previously moved by Artemis
- `%LOCALAPPDATA%\Artemis Toolkit`

A future installer may offer an optional checkbox to remove all Artemis settings/logs/state from `%LOCALAPPDATA%\Artemis Toolkit`, but that cleanup must be explicit and separate from removing the app itself.
