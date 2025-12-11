@echo off
cls
echo ==========================================
echo  Medical AutoRun Installer for Windows XP
echo ==========================================
echo.

:: 1. 관리자 권한 확인
net session >nul 2>&1
if %errorlevel%==1 (
    echo ERROR: This installer must be run as Administrator.
    pause
    exit /b
)

:: 2. 설치 폴더 생성
set INSTALLDIR=C:\MedicalAuto

if not exist "%INSTALLDIR%" (
    mkdir "%INSTALLDIR%"
)

echo Copying files...
copy medical.ahk "%INSTALLDIR%" >nul
copy AutoHotkey.exe "%INSTALLDIR%" >nul
copy run_medical.cmd "%INSTALLDIR%" >nul

echo Files copied.
echo.

:: 3. 기존 작업 삭제
echo Removing old scheduled task if exists...
schtasks /delete /tn MedicalAutoRun /f >nul 2>&1

:: 4. XP Pro에서 예약 작업 추가 (schtasks XP 호환 버전)
echo Creating scheduled task...

schtasks /create ^
 /tn "MedicalAutoRun" ^
 /tr "%INSTALLDIR%\run_medical.cmd" ^
 /sc onlogon ^
 /ru Administrator ^
 /rp "" >nul 2>&1

if %errorlevel%==0 (
    echo Scheduled task created successfully.
) else (
    echo ERROR creating scheduled task.
    pause
    exit /b
)

echo.
echo Installation completed!
echo Medical AutoRun will now execute at every logon.
echo.
pause
exit

:: 4.a XP Home에서 예약 작업 추가
:: copy "%INSTALLDIR%\run_medical.cmd" "C:\Documents and Settings\Administrator\Start Menu\Programs\Startup\"

