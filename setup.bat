@echo off

REM Verity if the virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo The virtual environment already exists.
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
python.exe -m pip install --upgrade pip
pip install -r requirements.txt

echo Installation completed.
pause
