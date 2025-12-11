@echo off
echo ==============================
echo  Building VibesFLAC v1.0.0
echo ==============================

REM Use your user-installed Python where PyInstaller lives
set PY="%USERPROFILE%\AppData\Roaming\Python\Python313\Scripts\pyinstaller.exe"

if not exist %PY% (
    echo ERROR: PyInstaller not found!
    pause
    exit /b
)

%PY% ^
 --noconfirm ^
 --clean ^
 --windowed ^
 --name "VibesFLACtoALAC" ^
 --icon=icon.ico ^
 --add-data "gui;gui" ^
 --add-data "core;core" ^
 --add-data "utils;utils" ^
 main.py

echo Done! EXE is in /dist/VibesFLACtoALAC/
pause
