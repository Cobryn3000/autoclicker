# AutoClicker

A fast, configurable auto clicker for Windows. Clicks the mouse or presses keys for you, with a global hotkey, automatic stop conditions and per-app rules.

## Installing

Run `setup.bat`. It downloads the latest `AutoClicker.exe` to `%LOCALAPPDATA%\AutoClicker` and adds Desktop and Start menu shortcuts.

You can also download `AutoClicker.exe` directly and run it. The first time it runs, it offers to install itself in the same way.

AutoClicker checks for updates when it starts (you can turn this off in **Settings**) and can update itself in one click.

## Using it

Set things up in the main window, then press **Start** or your hotkey (**F9** by default) anywhere. The line under the Start button summarizes what will happen. Settings are saved automatically.

### Click speed
- **Clicks per second** (up to 1000) or a **fixed interval** in hours, minutes, seconds and milliseconds.
- **Randomize each interval** by up to ± a number of milliseconds so clicks look less mechanical.
- **Wait before starting**: a countdown so you can move to the right window first.

### Click action
- **Mouse click**: left, right or middle button.
- **Keyboard key**: press any key or key combination (for example `Space` or `Ctrl + C`). Use **Record…** to choose it.
- **Single or double** clicks or presses.
- **Hold for**: how long each press is held down. It's shortened automatically at very high speeds so the click rate stays accurate.

### Repeat
- Until you stop it, after a set number of clicks, or after a set amount of time.

### Click position (mouse only)
- **Wherever the cursor is**, optionally locked in place while clicking.
- **A fixed position**: type X/Y or use **Pick on screen…**, then click the spot. You can have the cursor move back after each click so you can keep using the mouse.

### Hotkey
- Any key or combination (for example `F9` or `Ctrl + Shift + S`). Use **Record…** to set it.
- **Toggle**: press once to start and again to stop. **Hold**: clicks only while the hotkey is held down.
- **Exact match only**: when on, the hotkey only fires if no other modifier keys are held.

### Safety
- Stop when you press **Alt+Tab**.
- Stop if a **different window comes to the front** (AutoClicker remembers the window it's clicking in).
- **Stop zones**: move the mouse into a screen corner, a screen edge, or a custom area you draw on screen to stop instantly.
- AutoClicker never clicks on its own window. It pauses while the cursor is over it, so pressing Start with the mouse is safe.

### App filter
- **Never click in listed apps** (blocklist) or **only click in listed apps** (allowlist).
- Choose whether a blocked app **pauses** clicking until you're back in an allowed app, or **stops** it.
- **Edit app list…** shows apps with open windows (searchable). You can also type a program name like `notepad.exe`.

### Appearance and settings
- Dark mode, always on top and window opacity.
- Sections can be collapsed and reordered with the buttons on each card.
- **Settings**: start minimized, update checks, stop notifications, create shortcuts, open the settings folder, and reset everything to defaults.

Only one copy of AutoClicker runs at a time. Opening it again brings the existing window to the front.

## Windows Defender false positive

Windows Defender may flag this application as a trojan. This is a false positive that commonly occurs with PyInstaller-built executables.

**Why does this happen?**
- PyInstaller packages Python code in a way that antivirus software considers suspicious.
- The application uses keyboard and mouse automation, which triggers security alerts.
- The executable is not code-signed, and that costs me money as a developer to do.

**How to fix it**

Option 1: Add a Windows Defender exclusion (if you want to use the autoclicker)
1. Open Windows Security.
2. Go to "Virus & threat protection".
3. Click "Manage settings" under "Virus & threat protection settings".
4. Scroll down to "Exclusions" and click "Add or remove exclusions".
5. Click "Add an exclusion" → "File".
6. Select the AutoClicker.exe file.

Option 2: Don't use the autoclicker
1. Until I as the developer am able to code-sign this, it will be flagged as malware.

## Building from source

```
pip install -r requirements.txt
python main.py          # run from source
python build_exe.py     # build AutoClicker.exe (version comes from version.txt)
```

Code layout:

| File | Purpose |
|---|---|
| `main.py` | Entry point (DPI awareness, single-instance check) |
| `gui.py` | Main window and dialogs |
| `widgets.py` | Theme, tooltips, notifications, on-screen picker |
| `clicker_engine.py` | Click loop, timing, stop conditions and app filter |
| `hotkeys.py` | Global hotkey handling and key recording |
| `settings.py` | Saved settings (`%LOCALAPPDATA%\AutoClicker\config.json`) |
| `updater.py` | Update check, self-update and first-run install |
| `winutils.py` | Win32 helpers (ctypes) |

To release, bump `version.txt`, run `build_exe.py`, and publish `AutoClicker.exe`, `version.txt` and `README.md` to the public `Cobryn3000/autoclicker` repo. Installed copies update from there.
