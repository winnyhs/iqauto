@echo off
setlocal enabledelayedexpansion

echo =====================================
echo   MEDICAL.mdb EXPORT START
echo =====================================

REM --- Detect current script directory ---
set SCRIPT_DIR=%~dp0

REM Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM --- Target folder (relative to script folder) ---
set TARGET=%SCRIPT_DIR%\client_db

echo Script directory: %SCRIPT_DIR%
echo Target folder: %TARGET%

if not exist "%TARGET%" (
    echo Creating target folder: %TARGET%
    mkdir "%TARGET%"
)

REM --- Locate medical.exe directory ---
set MED_DIR=

REM ---
if exist "C:\Program Files (x86)\medical\medical.exe" (
    set "MED_DIR=C:\Program Files (x86)\medical"
    goto do_copy
)

REM ---
if exist "C:\Program Files\medical\medical.exe" (
    set "MED_DIR=C:\Program Files\medical"
    goto do_copy
)

REM ---
if exist "C:\medical\medical.exe" (
    set "MED_DIR=C:\medical"
    goto do_copy
)

:do_copy

REM ---
if "%MED_DIR%"=="" (
    echo ERROR: medical.exe not found in known directories.
    pause
    REM exit /b
)

echo medical.exe found at: %MED_DIR%

echo Copying MEDICAL.mdb to USB client_db folder...
copy /Y "%MED_DIR%\MEDICAL.mdb" "%TARGET%\MEDICAL.mdb"

echo EXPORT COMPLETED.
pause
