@echo off
echo SITG Video Trimmer - Windows Installation Script
echo ==============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.6 or higher from https://www.python.org/downloads/
    echo and make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Checking for FFmpeg...
where ffmpeg >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo FFmpeg is not installed or not in PATH.
    echo.
    echo Please install FFmpeg:
    echo 1. Download FFmpeg from https://ffmpeg.org/download.html
    echo 2. Extract the files to a folder (e.g., C:\ffmpeg)
    echo 3. Add the bin folder to your PATH environment variable
    echo    (e.g., C:\ffmpeg\bin)
    echo.
    echo After installing FFmpeg, run this script again.
    pause
    exit /b 1
)

echo.
echo Cleaning up old files...
if exist sitg_video_trimmer.py (
    echo Backing up original monolithic version to sitg_video_trimmer_original.py
    rename sitg_video_trimmer.py sitg_video_trimmer_original.py
)

echo.
echo Creating shortcut...
echo @echo off > run_sitg_trimmer.bat
echo python sitg_video_trimmer_new.py >> run_sitg_trimmer.bat

echo.
echo Installation complete!
echo.
echo To run SITG Video Trimmer:
echo run_sitg_trimmer.bat
echo   or
echo python sitg_video_trimmer_new.py
echo.

echo Starting SITG Video Trimmer...
python sitg_video_trimmer_new.py

pause
