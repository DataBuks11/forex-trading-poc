@echo off
echo ============================================
echo  ForexTrade MT5 Bridge Setup
echo ============================================
echo.

REM Step 1: Copy EA to MT5 Experts folder
set "EXPERTS=%APPDATA%\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts"
echo [1/4] Copying bridge.mq5 to MT5 Experts folder...
copy /Y "%~dp0bridge.mq5" "%EXPERTS%\" >nul
echo        Done.

REM Step 2: Kill any running MT5 and restart it (triggers EA auto-compile)
echo [2/4] Restarting MT5 to compile the EA...
taskkill /F /IM terminal64.exe >nul 2>&1
timeout /t 3 /nobreak >nul
start "" "C:\Program Files\MetaTrader 5\terminal64.exe" /portable
echo        MT5 restarted. Waiting for it to compile...

REM Step 3: Wait and check if compiled
echo [3/4] Waiting for compilation...
timeout /t 15 /nobreak >nul
if exist "%EXPERTS%\bridge.ex5" (
    echo        bridge.ex5 compiled successfully!
) else (
    echo        Auto-compile may have failed.
    echo        Please do this manually in MT5:
    echo        - Press Ctrl+N for Navigator
    echo        - Right-click ^> Refresh
    echo        - Drag "bridge" onto any chart and click OK
)

REM Step 4: Start the bridge
echo [4/4] Starting bridge...
echo.
python "%~dp0bridge.py"
pause
