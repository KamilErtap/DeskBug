# DeskBug

A quiet desktop companion for Windows 10/11. Raise Webby among your desktop icons, watch delicate silk connections grow, and give your spider a little care through the system tray.

## Run (PowerShell)

Python 3.11 or newer and an interactive Windows desktop are required. Development was verified with Python 3.14 and PySide6 6.12.0.

```powershell
cd C:\Users\kerta\OneDrive\Desktop\DeskBug
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If the virtual environment already exists, skip its creation. Click the DeskBug tray icon (it may be inside the hidden-icons menu) to visit Webby. Feed and Pet restore needs; Rest sends Webby home to recover energy over time. When no home is available Webby rests in place. Automatic sleep starts at low energy and ends at 60 energy. Close the panel to keep Webby running. Choose **Quit DeskBug** in the tray menu, or hold **Ctrl+Alt+Q**, to exit.

The panel offers animation pace (50–150%), pet visibility, and silk/nest visibility. Hiding Webby hides the complete overlay, while simulation and care continue. Pace changes movement and walking animation; needs and sleep recovery keep their normal timing. Stats use brief eased transitions.

## Local data and privacy

Existing `%LOCALAPPDATA%\DeskBug\pet_data.json`, `progress.json`, and `home.json` formats are preserved. `settings.json` stores preferences. Saves use temporary files followed by atomic replacement. Invalid fields fall back to safe defaults; read/write failures are logged. Back up this folder before development. A missing home icon does not overwrite its saved name; it is restored when the icon returns. Web connections remain session-only, as in the prototype.

Rotating diagnostics live in `deskbug.log` in the same directory (512 KiB, two backups). There is no telemetry, network feature, or gameplay access to desktop file contents. Windows Explorer controls are inspected for icon labels and positions only; files are never opened, moved, renamed, or deleted.

## Architecture and development

- `main.py`: overlay, behavior orchestration, screen lifecycle, tray wiring and shutdown. Importing it does not launch the application.
- `behavior.py`: deterministic movement, heading interpolation and stable web keys.
- `state.py`: UI-independent needs and validated preferences.
- `progression.py`: XP, stages, and compatible progression saves.
- `persistence.py`: atomic JSON access and bounded rotating logs.
- `desktop_icons.py`: read-only Windows Explorer integration.
- `webs.py`: bounded web construction, duplicate detection, and XP rewards.
- `graphics.py`: procedural spider, silk and nest painting.
- `pet_panel.py`: compact management panel and tray.

No new runtime dependency was added. Prefer small changes and keep simulation calculations independent of Qt where practical. Do not run development tests against real pet saves.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q main.py pet_panel.py desktop_icons.py graphics.py behavior.py webs.py state.py progression.py persistence.py
```

Tests isolate saves in temporary directories and use Qt's offscreen platform with mocked desktop icons. They cover progression, malformed saves, settings validation, movement bounds, needs, sleep recovery, duplicate webs, icon removal/rebinding, and rendering. Offscreen rendering may need an explicitly registered system font because the offscreen Windows backend does not discover fonts in some environments.

## Windows verification checklist and limits

The overlay intentionally stays on the **primary monitor**, preserving the prototype's tested coordinate conversion: physical Explorer coordinates / primary-screen device-pixel ratio, minus overlay origin. It refreshes icon positions every minute and on display changes, rebinds surviving webs by icon name, and removes connections whose icons disappeared. Empty desktops remain playable. Background needs run once a minute; resting or hidden simulation runs at a lower timer frequency.

Verify on a real Windows 10/11 desktop before release:

1. At 100%, 125%, and 150% scaling, check icon-center alignment and nest placement. `python coordinate_test.py` remains the interactive coordinate diagnostic.
2. Confirm clicks pass through Webby and webs, the overlay stays above ordinary windows, and cursor avoidance remains comfortable.
3. Move/remove/restore desktop icons; wait a minute. Confirm surviving silk moves and the saved home returns without modifying any files.
4. Change primary monitor, scaling and taskbar work area; disconnect/reconnect a display. Secondary-monitor roaming and mixed-DPI cross-monitor travel are not implemented.
5. Exercise tray open/close, every setting, automatic and requested sleep, restart persistence, tray Quit, Ctrl+C, and Ctrl+Alt+Q.
6. Measure CPU while moving, sleeping and hidden on target hardware. Full-overlay painting and synchronous Explorer scans can become costly on unusually large desktops; Explorer responsiveness is outside the app's control.

Offscreen tests cannot verify native click-through, Explorer coordinates, real tray behavior, global key polling, monitor hotplug, or perceived motion quality. Fullscreen exclusive games and secure desktops may cover the overlay. A second simultaneous DeskBug instance is not supported; avoid running two processes against the same saves.
