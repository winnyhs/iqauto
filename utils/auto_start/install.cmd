@echo off
setlocal

:: ---------------------------------------------
:: - MUST save this file as ANSI (Windows 1252)
:: - How to create install.sed newly and install.exe accordingly:
::   - Win + R --> iexpress.exe --> save sed under THE SAME folder
::   - Human-generated version is not accepted by iexpress 
::   - To identify the install file, type install.cmd, 
::     do not browse the pull-down option
:: - How to create install.exe again (with the existing install.sed) in cmd: 
::   iexpress /n install.sed
:: ---------------------------------------------

echo ===========================================
echo   Medical Auto Installer
echo   for XP / Win7 / Win10
echo ===========================================
echo.


:: ---------------- OS DETECTION ----------------
set isXP=0
ver | find "5.1" >nul
if %errorlevel%==0 (
    set isXP=1
    echo [INFO] Windows XP detected
) else (
    echo [INFO] Windows 7 / 10 / 11 detected
)
echo.

:: ---------------- INSTALL PATH ----------------
if exist "%ProgramFiles(x86)%" (
    set "installpath=C:\Program Files (x86)\medical_auto"
) else (
    set "installpath=C:\Program Files\medical_auto"
)

echo Install Folder = %installpath%
mkdir "%installpath%" 2>nul

echo Copying program files...
copy start_medical.exe "%installpath%\start_medical.exe" /Y >nul
echo.


:: ---------------- REMOVE OLD TASK ----------------
echo Removing previous task if exists...
schtasks /delete /tn "MedicalAutoStart" /f >nul 2>&1


:: ---------------- CREATE NEW SCHEDULED TASK ----------------
echo Creating Task Scheduler entry...

if %isXP%==1 (
    echo [INFO] XP detected ? using XP-compatible schtasks command...
    schtasks /create /tn "MedicalAutoStart" ^
      /tr "%installpath%\start_medical.exe 1" ^
      /sc onlogon /f
) else (
    echo [INFO] Win7/10 detected ? using RL HIGHEST...
    schtasks /create /tn "MedicalAutoStart" ^
      /tr "%installpath%\start_medical.exe 1" ^
      /sc onlogon /rl highest /np /f
)

if %errorlevel% neq 0 (
    echo [ERROR] Failed to create scheduled task!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Task Scheduler entry created.
echo Installation completed!
echo.

:: How to see the scheduled task
:: schtasks /query /tn "MedicalAutoStart" /v

:: pause
endlocal
:: exit /b 0
