@echo off
REM ============================================================
REM Windows启动脚本 - 自动检测并启动项目后端 (Uvicorn)
REM 支持：自动创建 .conda 环境 + 自动安装 uv
REM ============================================================

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set CONDA_PYTHON=%SCRIPT_DIR%..\.conda\python.exe

echo.
echo ==========================================
echo Starting backend (Windows)
echo ==========================================

REM 检查 .conda/python.exe 是否存在
if exist "%CONDA_PYTHON%" (
    echo ✅ Using project Python: %CONDA_PYTHON%
) else (
    echo ❌ Project Python not found at: %CONDA_PYTHON%
    echo.
    echo Please run: pnpm install:all
    echo Or manually create environment:
    echo   conda create -p .conda python=3.10 -y
    echo   .conda\python.exe -m pip install -U pip uv
    echo   .conda\python.exe -m uv sync
    echo.
    exit /b 1
)

REM 检查 Python 是否可执行
"%CONDA_PYTHON%" --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python executable not working: %CONDA_PYTHON%
    exit /b 1
)

REM 快速检查关键依赖是否已安装
"%CONDA_PYTHON%" -c "import uvicorn" >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Dependencies not installed! Please run: pnpm install:all
    echo.
    exit /b 1
)

echo ✅ Starting FastAPI server on http://0.0.0.0:5611 ...
cd /d "%SCRIPT_DIR%"
"%CONDA_PYTHON%" -m uvicorn main:app --reload --port 5611 --host 0.0.0.0

endlocal
