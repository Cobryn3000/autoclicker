AutoClicker



Features:

- Ability to switch between clicks per second and time between clicks

- Can left click, right click, and middle click

- Can double click

- Repeat until stopped or a set amount of times

- location selection or current cursor location

- Hotkey changing

- Auto updater

- Customizable random offset between clicks

Settings:

- Prevent mouse movement when clicking

- Dark mode

- Always on top

- Minimize on start



Windows Defender False Positive



Windows Defender may flag this application as a trojan. This is a false positive that commonly occurs with PyInstaller-built executables.



Why does this happen?

- PyInstaller packages Python code in a way that antivirus software considers suspicious

- The application uses keyboard and mouse automation, which triggers security alerts

- The executable is not code-signed, and that costs me money as a developer to do.



How to fix:



Option 1: Add Windows Defender Exclusion (If you want to use the autoclicker)

1. Open Windows Security

2. Go to "Virus \& threat protection"

3. Click "Manage settings" under "Virus \& threat protection settings"

4. Scroll down to "Exclusions" and click "Add or remove exclusions"

5. Click "Add an exclusion" → "File"

6. Select the AutoClicker.exe file

Option 2: Don't use the autoclicker

1. Until I as the developer am able to code-sign this, it will be flagged as malware.
