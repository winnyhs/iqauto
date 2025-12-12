@echo off
setlocal EnableDelayedExpansion

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
    set "installpath=C:\Program Files (x86)\start_medical"
) else (
    set "installpath=C:\Program Files\start_medical"
)

echo Install Folder = %installpath%
mkdir "%installpath%" 2>nul

:: ----------- SOURCE FILE LOCATION (IMPORTANT) ---------

:: IExpress extracts files into %CD%
set "src=%CD%"
echo Source Folder = %src%

echo Checking if XML exists in source folder: "%src%\start_medical_schd.xml"
dir "%src%\start_medical_schd.xml"

echo Copying program files...
copy "%src%\start_medical.exe" "%installpath%\start_medical.exe" /Y >nul
copy "%src%\start_medical_schd.xml" "%installpath%\start_medical_schd.xml" /Y >nul
echo.


:: ---------------- REMOVE OLD TASK ----------------
echo Removing previous task if exists...
schtasks /delete /tn "MedicalAutoStart" /f >nul 2>&1


:: ---------------- CREATE NEW SCHEDULED TASK ----------------
echo Creating Task Scheduler entry...

if %isXP%==1 (
    echo [INFO] XP detected – using XP-compatible schtasks...
    schtasks /create /tn "MedicalAutoStart" ^
        /tr "%installpath%\start_medical.exe 1" ^
        /sc onlogon /ru "%USERNAME%" /f
    goto task_done
) 

echo [INFO] Win7+ detected - creating a schtask from XML...

:: XML ???? (??? ?? ??? ???? ?)
set "xmlfile=%installpath%\start_medical_schd.xml"
echo XML file = %xmlfile%

copy /y "start_medical_schd.xml" "%xmlfile%" >nul

:: PowerShell? install path ??
powershell -command ^
    "(gc '%xmlfile%') -replace 'C:\\\\Program Files.*?start_medical', '%installpath%' | Set-Content '%xmlfile%'" 

:: XML ?? Task Scheduler ??
schtasks /create /tn "MedicalAutoStart" /xml "%xmlfile%" /f

del "%xmlfile%" >nul 2>&1

:task_done
    set result=%errorlevel%
    if %result% neq 0 (
        echo [ERROR] Failed to create scheduled task!
        pause
        rem exit /b 1
    )

    echo.
    echo [SUCCESS] Task Scheduler entry created.
    echo Installation completed!
    echo.

    endlocal
    :: pause
    rem exit /b 1