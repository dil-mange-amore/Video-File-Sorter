@echo off
echo Building Video Sorter...
echo.

REM Run PyInstaller
pyinstaller --onefile --name "Video Sorter" ^
  --hidden-import tkinterdnd2 ^
  --windowed ^
  --add-data "ffprobe_bin;ffprobe_bin" ^
  "Video Files Sorter.py"

echo.
echo Build complete! Check the 'dist' folder for the executable.
pause