@echo off
:: Hypixel Skyblock Scripts — Bootstrap Runner
:: Usage: run.bat <script_name>   (e.g. run.bat farming\pumpkin_farm)

if "%1"=="" (
    echo Usage: run.bat ^<script_name^>
    echo Example: run.bat farming\pumpkin_farm
    pause
    exit /b 1
)

echo [Bootstrap] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [Bootstrap] Installing dependencies...
python -m pip install -r requirements.txt --quiet

echo [Bootstrap] Launching script: %1
python scripts\%1.py %2 %3 %4

pause
