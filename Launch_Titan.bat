@echo off
TITLE NBA SNIPER V7.1 - MANUAL DEBUG MODE
COLOR 0A

:: 1. FORCE NAVIGATION (Critical)
cd /d "%~dp0"

echo ==============================================
echo   NBA SNIPER DIAGNOSTIC LAUNCHER
echo ==============================================
echo.
echo [STEP 1] Current Directory check:
echo %CD%
echo.
echo PRESS ENTER TO START INSTALLATION...
pause

:: 2. INSTALL
echo.
echo [STEP 2] Installing Requirements...
py -3.11 -m pip install -r requirements.txt
echo Done.
pause

:: 3. DATA
echo.
echo [STEP 3] Running Data Fixer...
py -3.11 fix_data.py
echo Done.
pause

:: 4. BRAIN
echo.
echo [STEP 4] Running Brain Surgery (API Connection)...
py -3.11 fix_brain.py
echo Done.
pause

:: 5. LAUNCH
echo.
echo [STEP 5] Launching App...
py -3.11 -m streamlit run app.py

:: 6. FINAL CATCH
echo.
echo App closed.
pause