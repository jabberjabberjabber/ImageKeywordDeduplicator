@echo off
setlocal enabledelayedexpansion

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python and try again.
    exit /b 1
)

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Download NLTK data
echo Downloading NLTK data...
python -c "import nltk; nltk.download('wordnet')"

REM Run the script
echo Running the script...
cls
echo This script will OVERWRITE all keyword metadata in the directory tree you specify!
echo Hit CTRL-C to EXIT. Last warning!
pause 
python key-dedupe.py
pause
REM Deactivate virtual environment
deactivate

echo Done!

