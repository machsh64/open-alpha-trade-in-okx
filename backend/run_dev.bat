@echo off
REM Windows启动脚本 - 用于开发环境
REM 自动查找项目Python并启动uvicorn

set PYTHONPATH=%cd%

REM 检查 .conda/python.exe 是否存在
if exist "%~dp0..\.conda\python.exe" (
    echo Using project Python: %~dp0..\.conda\python.exe
    "%~dp0..\.conda\python.exe" -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
) else (
    echo Project Python not found at ../.conda/python.exe
    echo Please run: pnpm install:all
    echo Or use system Python: python -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
    python -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
)

