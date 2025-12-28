@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 🚀 Updating Founder OS...
git pull
if %ERRORLEVEL% EQU 0 (
    echo ✅ Code updated!
    echo 📦 Installing dependencies...
    python -m pip install -q -r requirements.txt
    echo.
    echo ✅ UPDATE COMPLETE!
    echo.
    echo Please restart Cursor to apply changes.
    pause
) else (
    echo ❌ Update failed. Check your internet connection.
    pause
)

