\# AutoClicker



\## Windows Defender False Positive



Windows Defender may flag this application as a trojan. This is a \*\*false positive\*\* that commonly occurs with PyInstaller-built executables.



\### Why does this happen?

\- PyInstaller packages Python code in a way that antivirus software considers suspicious

\- The application uses keyboard and mouse automation, which triggers security alerts

\- The executable is not code-signed, and that costs me money as a developer to do.



\### How to fix:



\*\*Option 1: Add Windows Defender Exclusion (Recommended)\*\*

1\. Open Windows Security

2\. Go to "Virus \& threat protection"

3\. Click "Manage settings" under "Virus \& threat protection settings"

4\. Scroll down to "Exclusions" and click "Add or remove exclusions"

5\. Click "Add an exclusion" → "File"

6\. Select the AutoClicker.exe file

