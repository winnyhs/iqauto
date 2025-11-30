@echo off
setlocal enableextensions

:: -----------------------------------------------------------
:: 1) 관리자 권한 확인 및 상승 (UAC)
:: -----------------------------------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~0' -Verb runAs"
    exit /b
)

echo --------------------------------------------
echo  Analyzer Installer (Admin Mode)
echo --------------------------------------------

:: -----------------------------------------------------------
:: 2) 설치 경로 설정
:: -----------------------------------------------------------
set TARGET=C:\analyzer

echo Installing to: %TARGET%
if not exist "%TARGET%" (
    mkdir "%TARGET%"
)

:: -----------------------------------------------------------
:: 3) Users 그룹에 Modify 권한 부여
:: -----------------------------------------------------------
echo Setting ACL permissions for Users...
icacls "%TARGET%" /grant Users:(OI)(CI)M /T >nul

:: -----------------------------------------------------------
:: 4) 파일 복사 (현재 디렉토리/app → C:\analyzer)
:: -----------------------------------------------------------
echo Copying files...
xcopy /E /I /Y "%~dp0app" "%TARGET%\app" >nul

:: -----------------------------------------------------------
:: 5) symlink 생성 (선택)
:: 예: analyzer\data → analyzer\app\data
:: -----------------------------------------------------------

:: echo Creating symlink...
:: mklink /D "%TARGET%\data" "%TARGET%\app\data"

echo Installation completed.
pause

