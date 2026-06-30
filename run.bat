@echo off
REM SlideCraft Lite launcher (Windows). Low-RAM build.
REM Usage:   run.bat
REM          set HOST=0.0.0.0 && run.bat   (LAN-accessible)
setlocal
chcp 65001 >NUL
cd /d "%~dp0"

REM --- One-time setup: only runs when venv is missing ---
if not exist .venv\Scripts\activate.bat (
    echo ^>^> First run: creating .venv
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create venv. Install Python 3.10+ and add it to PATH.
        pause
        exit /b 1
    )
    echo ^>^> Installing deps ^(no torch, no ffmpeg -- ~250 MB^)...
    .venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo ERROR: dependency install failed. See output above.
        pause
        exit /b 1
    )
    copy /y requirements.txt .venv\.installed >NUL
    goto run
)

REM --- Re-install only if requirements.txt changed since last install ---
fc /b requirements.txt .venv\.installed >NUL 2>&1
if errorlevel 1 (
    echo ^>^> requirements.txt changed -- updating deps...
    .venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
    copy /y requirements.txt .venv\.installed >NUL
)

:run
REM --- LibreOffice is OPTIONAL in Lite. PDF upload + every export work without it.
REM     Only PPTX upload needs LibreOffice (PPTX -> PDF -> JPG). Warn but never auto-install.
if not exist "C:\Program Files\LibreOffice\program\soffice.exe" (
    where soffice >NUL 2>&1
    if errorlevel 1 (
        echo.
        echo [info] LibreOffice not found -- PDF upload still works.
        echo        For PPTX upload, install: winget install TheDocumentFoundation.LibreOffice
        echo.
    )
)

.venv\Scripts\python.exe app.py
endlocal
