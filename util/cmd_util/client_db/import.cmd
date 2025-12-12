@echo off
setlocal enabledelayedexpansion

echo =====================================
echo   MEDICAL.mdb IMPORT START
echo =====================================

REM --- Detect script directory ---
set SCRIPT_DIR=%~dp0

REM Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM --- Source mdb from USB ---
set SOURCE=%SCRIPT_DIR%\client_db\MEDICAL.mdb

echo Script directory: %SCRIPT_DIR%
echo Source file: %SOURCE%

REM --- Check the source file exists
if not exist "%SOURCE%" (
    echo ERROR: MEDICAL.mdb not found in client_db folder.
    pause
    REM exit /b
)

REM --- Locate medical.exe directory ---
set MED_DIR=

if exist "C:\Program Files (x86)\medical\medical.exe" (
    set "MED_DIR=C:\Program Files (x86)\medical"
    goto do_copy
)
if exist "C:\Program Files\medical\medical.exe" (
    set "MED_DIR=C:\Program Files\medical"
    goto do_copy
)
if exist "C:\medical\medical.exe" (
    set "MED_DIR=C:\medical"
    goto do_copy
)

:do_copy

REM --- Check the medical folder exists
if "%MED_DIR%"=="" (
    echo ERROR: medical.exe not found in known directories.
    pause
    REM exit /b
)

echo medical.exe found at: %MED_DIR%

REM --- Backup existing MEDICAL.mdb ---
if exist "%MED_DIR%\MEDICAL_org.mdb" (
    echo Deleting existing MEDICAL_org.mdb...
    del /F /Q "%MED_DIR%\MEDICAL_org.mdb"
)

REM --- Backup MEDICAL.mdb
if exist "%MED_DIR%\MEDICAL.mdb" (
    echo Renaming MEDICAL.mdb to MEDICAL_org.mdb...
    ren "%MED_DIR%\MEDICAL.mdb" "MEDICAL_org.mdb"
)

REM --- Copy new MEDICAL.mdb from USB ---
echo Copying MEDICAL.mdb to medical directory...
copy /Y "%SOURCE%" "%MED_DIR%\MEDICAL.mdb"

echo IMPORT COMPLETED.
pause
