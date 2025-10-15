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
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\AutoClicker.lnk"

:: Create AppData directory if it doesn't exist
echo [1/5] Creating installation directory...
if not exist "%APPDATA_DIR%" (
    mkdir "%APPDATA_DIR%"
    echo Created directory: %APPDATA_DIR%
) else (
    echo Directory already exists: %APPDATA_DIR%
)
echo.

:: Download the latest AutoClicker.exe
echo [2/5] Downloading latest AutoClicker.exe...
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
set "DOWNLOAD_ERROR=%ERRORLEVEL%"
del "%TEMP_PS%" 2>nul

if %DOWNLOAD_ERROR% NEQ 0 (
    echo.
    echo ERROR: Failed to download AutoClicker.exe
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)
echo.

:: Verify the file was downloaded
echo [3/5] Verifying download...
if exist "%EXE_PATH%" (
    echo File downloaded successfully!
    for %%A in ("%EXE_PATH%") do echo File size: %%~zA bytes
) else (
    echo ERROR: Downloaded file not found!
    pause
    exit /b 1
)
echo.

:: Download version.txt to AppData
echo [4/5] Downloading additional files...
echo Downloading version information...
set "TEMP_PS=%TEMP%\download_version.ps1"
(
echo $ProgressPreference = 'SilentlyContinue'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/%GITHUB_REPO%/main/version.txt' -OutFile '%APPDATA_DIR%\version.txt' -UserAgent 'AutoClicker-Setup' -ErrorAction Stop } catch { }
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%" 2>nul
del "%TEMP_PS%" 2>nul

:: Download README.md to AppData
echo Downloading README...
set "TEMP_PS=%TEMP%\download_readme.ps1"
(
echo $ProgressPreference = 'SilentlyContinue'
echo [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
echo try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/%GITHUB_REPO%/main/README.md' -OutFile '%APPDATA_DIR%\README.md' -UserAgent 'AutoClicker-Setup' -ErrorAction Stop } catch { }
) > "%TEMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP_PS%" 2>nul
del "%TEMP_PS%" 2>nul
echo.

:: Launch AutoClicker
echo [5/5] Launching AutoClicker...
echo.
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
