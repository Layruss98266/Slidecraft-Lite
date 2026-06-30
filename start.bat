@echo off
REM SlideCraft Lite — fast launcher. Skips setup if .venv exists; uses venv
REM Python directly. Delegates to run.bat on first run.
cd /d "%~dp0"
title SlideCraft Lite

if not exist ".venv\Scripts\python.exe" (
    echo [setup] First run - launching run.bat for setup...
    call "%~dp0run.bat"
    exit /b %errorlevel%
)

REM LibreOffice is optional in Lite. PDF upload + every export work without it.
REM Only PPTX upload needs it. No auto-install — just inform.
if not exist "C:\Program Files\LibreOffice\program\soffice.exe" (
    where soffice >NUL 2>&1
    if errorlevel 1 (
        echo [info] LibreOffice not found - PDF upload still works.
        echo        For PPTX upload: winget install TheDocumentFoundation.LibreOffice
    )
)

echo [start] http://127.0.0.1:5050
.venv\Scripts\python.exe app.py
if errorlevel 1 (
    echo ERROR: Server exited unexpectedly. See above.
    pause
)
