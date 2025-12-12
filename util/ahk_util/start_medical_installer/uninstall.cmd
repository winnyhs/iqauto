@echo off
setlocal

echo ===========================================
echo   Medical Auto Uninstaller
echo ===========================================
echo.

echo Removing scheduled task...
schtasks /delete /tn "MedicalAutoStart" /f >nul 2>&1

echo Removing install folder...
rmdir /s /q "C:\Program Files (x86)\medical_auto" 2>nul
rmdir /s /q "C:\Program Files\medical_auto" 2>nul

echo.
echo Uninstall completed successfully!
echo.

:: How to see the scheduled task
:: schtasks /query /tn "MedicalAutoStart" /v

:: pause
endlocal
:: exit /b 0
