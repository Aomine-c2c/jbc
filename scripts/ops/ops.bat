@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%backend\.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%backend\.venv\Scripts\python.exe" "%SCRIPT_DIR%ops" %*
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%ops" %*
) else (
    python "%SCRIPT_DIR%ops" %*
)
endlocal
