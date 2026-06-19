@echo off
echo Setting up AI-Based Business Lead Discovery System...

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

echo.
echo Setup Complete!
echo To start the tool, make sure the virtual environment is activated and run:
echo python main.py
echo.
pause