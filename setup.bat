@echo off
setlocal enabledelayedexpansion

echo ========================================
echo AutoClicker Setup
echo ========================================
echo.

:: Set variables
set "GITHUB_REPO=Cobryn3000/autoclicker"
set "EXE_URL=https://raw.githubusercontent.com/%GITHUB_REPO%/main/AutoClicker.exe"
set "APPDATA_DIR=%LOCALAPPDATA%\AutoClicker"
set "EXE_PATH=%APPDATA_DIR%\AutoClicker.exe"

:: Get the correct Desktop path using PowerShell
echo [1/7] Detecting desktop location...
set "TEMP_PS=%TEMP%\get_desktop.ps1"
(
echo $desktop = [Environment]::GetFolderPath('Desktop')
echo Write-Output $desktop
) > "%TEMP_PS%"
for /f "delims=" %%I in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"') do set "DESKTOP=%%I"
del "%TEMP_PS%" 2>nul

if "%DESKTOP%"=="" (
    echo WARNING: Could not detect desktop path, using default.
    set "DESKTOP=%USERPROFILE%\Desktop"
)

set "SHORTCUT=%DESKTOP%\AutoClicker.lnk"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "STARTMENU_SHORTCUT=%STARTMENU_DIR%\AutoClicker.lnk"
echo Desktop path: %DESKTOP%
echo Start Menu path: %STARTMENU_DIR%
echo.

:: Create AppData directory if it doesn't exist
echo [2/7] Creating installation directory...
if not exist "%APPDATA_DIR%" (
    mkdir "%APPDATA_DIR%" 2>nul
    if exist "%APPDATA_DIR%" (
        echo Created directory: %APPDATA_DIR%
    ) else (
        echo ERROR: Failed to create directory: %APPDATA_DIR%
        pause
        exit /b 1
    )
) else (
    echo Directory already exists: %APPDATA_DIR%
)
echo.

:: Download the latest AutoClicker.exe
echo [3/7] Downloading latest AutoClicker.exe...
echo From: %EXE_URL%
echo To: %EXE_PATH%

:: Create temporary PowerShell script
set "TEMP_PS=%TEMP%\download_autoclicker.ps1"
(
echo $ProgressPreference = 'SilentlyContinue'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo try {
echo     Invoke-WebRequest -Uri '%EXE_URL%' -OutFile '%EXE_PATH%' -UserAgent 'AutoClicker-Setup' -ErrorAction Stop
echo     Write-Host 'Download successful!' -ForegroundColor Green
echo     exit 0
echo } catch {
echo     Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Red
echo     exit 1
echo }
) > "%TEMP_PS%"

:: Run PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"
set "DOWNLOAD_ERROR=!ERRORLEVEL!"
del "%TEMP_PS%" 2>nul

if !DOWNLOAD_ERROR! NEQ 0 (
    echo.
    echo ERROR: Failed to download AutoClicker.exe
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo.

:: Verify the file was downloaded
echo [4/7] Verifying download...
if exist "%EXE_PATH%" (
    echo File downloaded successfully!
    for %%A in ("%EXE_PATH%") do set "FILE_SIZE=%%~zA"
    echo File size: !FILE_SIZE! bytes
    
    if !FILE_SIZE! LSS 1000 (
        echo WARNING: File size seems unusually small, download may be corrupted.
    )
) else (
    echo ERROR: Downloaded file not found!
    pause
    exit /b 1
)
echo.

:: Download version.txt to AppData
echo [5/7] Downloading additional files...
echo Downloading version information...
set "TEMP_PS=%TEMP%\download_version.ps1"
(
echo $ProgressPreference = 'SilentlyContinue'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo try { 
echo     Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/%GITHUB_REPO%/main/version.txt' -OutFile '%APPDATA_DIR%\version.txt' -UserAgent 'AutoClicker-Setup' -ErrorAction Stop 
echo     Write-Host 'Version file downloaded successfully'
echo } catch { 
echo     Write-Host 'Warning: Could not download version file'
echo }
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%" 2>nul
del "%TEMP_PS%" 2>nul

:: Download README.md to AppData
echo Downloading README...
set "TEMP_PS=%TEMP%\download_readme.ps1"
(
echo $ProgressPreference = 'SilentlyContinue'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo try { 
echo     Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/%GITHUB_REPO%/main/README.md' -OutFile '%APPDATA_DIR%\README.md' -UserAgent 'AutoClicker-Setup' -ErrorAction Stop 
echo     Write-Host 'README downloaded successfully'
echo } catch { 
echo     Write-Host 'Warning: Could not download README'
echo }
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%" 2>nul
del "%TEMP_PS%" 2>nul
echo.

:: Create desktop shortcut
echo [6/7] Creating desktop shortcut...
set "TEMP_PS=%TEMP%\create_shortcut.ps1"
(
echo $WshShell = New-Object -comObject WScript.Shell
echo $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%')
echo $Shortcut.TargetPath = '%EXE_PATH%'
echo $Shortcut.WorkingDirectory = '%APPDATA_DIR%'
echo $Shortcut.Save()
echo Write-Host 'Shortcut created successfully: %SHORTCUT%'
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%" 2>nul
set "SHORTCUT_ERROR=!ERRORLEVEL!"
del "%TEMP_PS%" 2>nul

if !SHORTCUT_ERROR! NEQ 0 (
    echo WARNING: Could not create desktop shortcut.
) else (
    echo Shortcut created on desktop: AutoClicker.lnk
)
echo.

:: Create Start Menu shortcut
echo [7/7] Creating Start Menu shortcut...
set "TEMP_PS=%TEMP%\create_startmenu_shortcut.ps1"
(
echo $WshShell = New-Object -comObject WScript.Shell
echo $Shortcut = $WshShell.CreateShortcut^('%STARTMENU_SHORTCUT%'^)
echo $Shortcut.TargetPath = '%EXE_PATH%'
echo $Shortcut.WorkingDirectory = '%APPDATA_DIR%'
echo $Shortcut.Save^(^)
echo Write-Host 'Start Menu shortcut created successfully'
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%"
set "STARTMENU_ERROR=!ERRORLEVEL!"
del "%TEMP_PS%" 2>nul

if !STARTMENU_ERROR! NEQ 0 (
    echo WARNING: Could not create Start Menu shortcut.
) else (
    echo Shortcut created in Start Menu: AutoClicker.lnk
)
echo.

:: Launch AutoClicker
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo AutoClicker installed to: %APPDATA_DIR%
echo.
echo Starting AutoClicker...
timeout /t 2 /nobreak > nul

start "" "%EXE_PATH%"

echo.
echo Setup completed successfully!
echo You can close this window.
timeout /t 3 /nobreak > nul
exit /b 0