@echo off
setlocal
cd /d %~dp0
chcp 65001 >nul

echo Starting XueZhi Portrait learning system...
echo.
REM --- Auto-load .env from project root (.env is ignored by git) ---
if exist ".env" (
  echo .env detected. XFYUN settings will be loaded securely.
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
) else (
  echo [WARN] .env not found. To enable XFYUN PPT features, copy .env.example to .env and fill in your own credentials.
)
echo.

REM --- Pick Python interpreter: prefer .venv, then system python ---
set "PYEXE="
if exist ".\.venv\Scripts\python.exe" set "PYEXE=.\.venv\Scripts\python.exe"
if "%PYEXE%"=="" if exist ".\venv\Scripts\python.exe" set "PYEXE=.\venv\Scripts\python.exe"
if "%PYEXE%"=="" set "PYEXE=python"

echo Using Python: %PYEXE%
echo.
echo Launching web server...
echo Open in browser: http://127.0.0.1:5000
echo.

REM Keep Python in UTF-8 mode for stable Windows behavior
set PYTHONUTF8=1
"%PYEXE%" run.py

pause
