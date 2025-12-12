@echo off

setlocal

:: =====================================================
:: Force Working Directory = script folder
:: =====================================================
cd /d "%~dp0"

:: =====================================================
:: Prevent infinite loop after elevation
:: =====================================================
if "%~1"=="__elevated" goto :elevated

:: =====================================================
:: Check admin privileges
:: =====================================================
net session >nul 2>&1
if %errorlevel%==0 (
    echo Already running with administrator privileges...
    goto elevated
)

:: =====================================================
:: XP detection - cannot auto elevate, must be an admin account
:: =====================================================
ver | find "5.1" >nul 2>&1
if %errorlevel%==0 (
    echo.
    echo [ERROR] Windows XP에서는 자동 관리자 승격이 불가능합니다.
    echo 관리자 계정으로 로그인하고 스크립트를 다시 실행해 주세요.
    echo.
    pause
    exit /b
)

:: =====================================================
:: Auto Elevation for Windows 7 / 10
:: =====================================================
echo Requesting administrator privileges...
set "vbs=%temp%\getadmin.vbs"
echo Set UAC = CreateObject("Shell.Application") > "%vbs%"
echo UAC.ShellExecute "%~f0", "__elevated", "", "runas", 1 >> "%vbs%"
cscript //nologo "%vbs%"
del "%vbs%"
exit /b

:: =====================================================
:elevated
echo Running with administrator privileges...
echo.

:: =====================================================
::  AHK COMPILE SECTION (your logic)
:: =====================================================
"..\bin\Ahk2Exe.exe" ^
  /in "start_medical.ahk" /out "start_medical.exe" /icon "medical.ico" ^
  /base "..\bin\ANSI 32-bit.bin"
:: "..\bin\Ahk2Exe.exe" /in "start_medical.ahk" /out "auto_start.exe" /base "..\bin\ANSI 32-bit.bin"

echo Compile Completed!
echo.

copy ".\start_medical.exe" "..\start_medical_installer\" /Y
echo Copy completed: start_medical.exe into start_medical_installer


:: pause
:: exit /b

:: 
:: 컴파일된 exe를 Windows 부팅 시 자동실행되도록 작업스케쥴러에 연결하는 
:: CMD command
:: schtasks /create /tn "AutoStartMedical" ^
::  /tr "\"C:\MedicalAuto\start_medical.exe\" 1" ^
::  /sc onlogon  /rl highest /f
