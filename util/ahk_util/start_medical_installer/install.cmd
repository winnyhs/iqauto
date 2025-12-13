@echo off
setlocal EnableDelayedExpansion

:: ---------------------------------------------
:: MUST be saved in ANSI Windows 1252
:: ---------------------------------------------

echo ===========================================
echo   Medical Auto Installer
echo   for XP / Win7 / Win10
echo ===========================================
echo.

:: -----------------------------------------------
:: Set up 
:: -----------------------------------------------
:: ----- OS DETECTION 
set isXP=0
ver | find "5.1" >nul
if %errorlevel%==0 (
    set isXP=1
    echo [INFO] Windows XP detected
) else (
    echo [INFO] Windows 7 / 10 / 11 detected
)
echo.

:: ----- SOURCE FILE LOCATION (IMPORTANT)
:: IExpress extracts files into %CD%
set "src=%CD%"
echo Install Source Folder = %src%
echo.

:: ----- INSTALL PATH 
:: ( and ) easily breaks the script.
:: So, change the install directory when needed
if exist "%ProgramFiles(x86)%" (
    set "installPath=C:\Program Files (x86)\start_medical"
) else (
    set "installPath=C:\Program Files\start_medical"
)
:: set "installPath=C:\start_medical"
echo Install Path      = %installPath%

set exeFile=start_medical.exe
set xmlFile=start_medical_schd.xml
set iconFile=medical.ico
set "readLinkFile=Medical_read.lnk"
set "startLinkFile=Medical_start.lnk"

set "exePath=%installPath%\%exeFile%"
set "xmlPath=%installPath%\%xmlFile%"
echo Installed exePath = %exePath%
echo Installed xmlPath = %xmlPath%

:: ----- Desktop path for XP/7/10 
for /f "tokens=2,*" %%a in (
    'reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop 2^>nul'
) do (
    set "DESKTOP=%%b"
)
:: set DESKTOP=%DESKTOP:"=%
:: Force expand environment variables inside DESKTOP
call set DESKTOP=%DESKTOP%
echo Desktop Path      = %DESKTOP%
echo.


:: -------------------------------------------------------
::  Start 
:: -------------------------------------------------------

:: ----- 1. Prepare installPath - copy files
:: echo Checking if XML exists in source folder: "%src%\start_medical_schd.xml"
:: dir "%src%\%xmlFile%"
echo Creating the install folder...
mkdir "%installPath%" 2>nul

echo Copying files into the install folder...
copy "%src%\%exeFile%"       "%installPath%\%exeFile%" /Y >nul
copy "%src%\%xmlFile%"       "%installPath%\%xmlFile%" /Y >nul
copy "%src%\%iconFile%"      "%installPath%\%iconFile%" /Y >nul
copy "%src%\%readLinkFile%"  "%installPath%\%readLinkFile%" /Y >nul
copy "%src%\%startLinkFile%" "%installPath%\%startLinkFile%" /Y >nul


:: ----- 2. Add the task into system scheduler
:: ----- REMOVE OLD TASK 
echo Removing the previous task if exists...
schtasks /delete /tn "MedicalAutoStart" /f >nul 2>&1

:: ----- CREATE NEW SCHEDULED TASK 
echo Creating a Task Scheduler entry...
if %isXP%==1 (
    echo [INFO] XP detected - using XP-compatible schtasks...
    schtasks /create /tn "MedicalAutoStart" ^
        /tr "%exePath% 1" ^
        /sc onlogon /ru "%USERNAME%" /f
    goto schd_done
) 

echo [INFO] Win7+ detected - creating a schtask from XML...
:: ----- XML descriptor for system scheduler
:: echo XML Descriptor for Scheduler = %xmlPath%
copy /y "start_medical_schd.xml" "%xmlPath%" >nul

:: install path for the XML descritor for system scheduler
powershell -command ^
    "(gc '%xmlPath%') -replace 'C:\\\\Program Files.*?start_medical', '%installPath%' | Set-Content '%xmlPath%'" 

:: Add the task into the system task scheduler
schtasks /create /tn "MedicalAutoStart" /xml "%xmlPath%" /f

del "%xmlPath%" >nul 2>&1


:schd_done
:: ----- 3. Create a link on Desktop

:: ----- Create StartMedical.vbs to generate shortcuts
:: - CMD parses the whole code block by ( ... ) > file at a time.  
::   In this case, it's hard to parse (, ), ", ", space, or so. 
::   Do it with line-by-line redirection, instead of code block
:: - Code generation by these ways can't write Korean. 
:: - TODO: check on WinXP that ^& works. try &. 
:: set vbsPath=%TEMP%\make_shortcut.vbs
:: >  "%vbsPath%" echo Set oWS = CreateObject^(^"WScript.Shell^"^)
:: >> "%vbsPath%" echo desktop = oWS.ExpandEnvironmentStrings^(^"%DESKTOP%^"^)
:: >> "%vbsPath%" echo. 
:: >> "%vbsPath%" echo ---- Shortcut #1 : start_medical.exe ----
:: >> "%vbsPath%" echo Set Lnk1 = oWS.CreateShortcut^(desktop ^& ^"\StartMedical_PLACEHOLDER.lnk^"^)
:: >> "%vbsPath%" echo Lnk1.TargetPath = ^"%TARGET_EXE%^"
:: >> "%vbsPath%" echo Lnk1.WorkingDirectory = ^"%installPath%^"
:: >> "%vbsPath%" echo Lnk1.Arguments = ^"^"
:: >> "%vbsPath%" echo Lnk1.IconLocation = ^"%iconFile%^"
:: >> "%vbsPath%" echo Lnk1.Save
:: >> "%vbsPath%" echo.
:: >> "%vbsPath%" echo ---- Shortcut #2 : start_medical.exe 1 ----
:: >> "%vbsPath%" echo Set Lnk2 = oWS.CreateShortcut^(desktop ^& ^"\ReadMedical_PLACEHOLDER.lnk^"^)
:: >> "%vbsPath%" echo Lnk2.TargetPath = ^"%TARGET_EXE%^"
:: >> "%vbsPath%" echo Lnk2.WorkingDirectory = ^"%installPath%^"
:: >> "%vbsPath%" echo Lnk2.IconLocation = ^"%iconFile%^"
:: >> "%vbsPath%" echo Lnk2.Arguments = ^"1^"
:: >> "%vbsPath%" echo Lnk2.Save
:: set vbsPath=%src%\install_link.vbs
:: echo vbsPath      = %vbsPath%
:: "" is required because the install path has space, (, and )
echo readLinkFile = "%installPath%\%readLinkFile%" "%DESKTOP%%\%readLinkFile%"
copy "%installPath%\%readLinkFile%" "%DESKTOP%\%readLinkFile%"

echo startLinkFile = "%installPath%\%startLinkFile%" "%DESKTOP%\%startLinkFile%"
copy "%installPath%\%startLinkFile%" "%DESKTOP%\%startLinkFile%"
echo Shortcuts created on Desktop.


:: ----- 4. Wrap-up -----
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