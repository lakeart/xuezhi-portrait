@echo off
setlocal
cd /d %~dp0

echo 正在启动学智画像：教育大数据赋能高校学情可视分析系统...
echo.
REM --- 自动加载项目根目录 .env（.env 已在 .gitignore 中忽略，不会提交）---
if exist ".env" (
  echo 已检测到 .env（将自动加载讯飞配置；不会输出密钥）
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
) else (
  echo [WARN] 未检测到 .env：如需启用讯飞智文PPT，请将 .env.example 复制为 .env 并填入自己的 XFYUN_ZW_APP_ID / XFYUN_ZW_API_SECRET
)
echo.

REM --- 选择 Python 解释器：优先 Anaconda，其次 .venv/venv，最后系统 python ---
set "PYEXE="
if exist "D:\AnacondaEnvs\pytorch\python.exe" set "PYEXE=D:\AnacondaEnvs\pytorch\python.exe"
if "%PYEXE%"=="" if exist ".\.venv\Scripts\python.exe" set "PYEXE=.\.venv\Scripts\python.exe"
if "%PYEXE%"=="" if exist ".\venv\Scripts\python.exe" set "PYEXE=.\venv\Scripts\python.exe"
if "%PYEXE%"=="" set "PYEXE=python"

echo 使用 Python: %PYEXE%
"%PYEXE%" run.py

pause