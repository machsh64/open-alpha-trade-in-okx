@echo off
REM ============================================================
REM Windows启动脚本 - 自动检测并启动项目后端 (Uvicorn)
REM 支持：自动创建 .conda 环境 + 自动安装 uv
REM ============================================================

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0
set CONDA_PYTHON=%SCRIPT_DIR%..\ .conda\python.exe
set CONDA_PYTHON=%CONDA_PYTHON: =%

echo.
echo ==========================================
echo Starting backend (Windows)
echo ==========================================

REM 检查 .conda/python.exe 是否存在
if exist "%CONDA_PYTHON%" (
    echo Using project Python: %CONDA_PYTHON%
) else (
    echo Project Python not found at %CONDA_PYTHON%
    echo Checking for conda...
    where conda >nul 2>nul
    if %errorlevel% neq 0 (
        echo Conda not found! Please install Miniconda first:
        echo    https://docs.conda.io/en/latest/miniconda.html
        pause
        exit /b 1
    )
    echo Creating new conda environment...
    call conda create -p "%SCRIPT_DIR%..\ .conda" python=3.10 -y
    echo Installing uv...
    call "%SCRIPT_DIR%..\ .conda\python.exe" -m pip install -U pip uv
)

echo  Checking dependencies with uv...
call "%SCRIPT_DIR%..\ .conda\python.exe" -m uv sync --quiet

echo  Starting FastAPI server...
call "%SCRIPT_DIR%..\ .conda\python.exe" -m uvicorn main:app --reload --port 5611 --host 0.0.0.0

endlocal
