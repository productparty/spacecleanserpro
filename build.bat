@echo off
REM Build script for creating Space Cleanser Pro executable locally
REM This allows developers to test the .exe before creating a GitHub release

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --add-data "folder_defs.json;." --name "SpaceCleanserPro" main.py

echo.
echo Build complete! Check dist\SpaceCleanserPro.exe
echo.
pause
