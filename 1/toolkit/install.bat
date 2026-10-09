@echo off
REM ================================================================
REM INSTALLATEUR TOOLKIT v2.0.0 - WINDOWS
REM ================================================================
setlocal

echo [1/6] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python non installe. Telechargez Python 3.9+ sur python.org
    pause
    exit /b 1
)

echo [2/6] Creation du virtualenv .venv...
if not exist ".venv" (
    python -m venv .venv
)

echo [3/6] Activation du virtualenv...
call .venv\Scripts\activate.bat

echo [4/6] Mise a jour de pip...
python -m pip install --upgrade pip

echo [5/6] Installation des dependances...
pip install -r requirements.txt

echo [6/6] Creation de l'arborescence...
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "payloads" mkdir payloads
if not exist "payloads\mail_templates" mkdir payloads\mail_templates

echo.
echo [+] Installation terminee.
echo [+] Lancement : .venv\Scripts\activate ^&^& python toolkit.py --help
pause
endlocal