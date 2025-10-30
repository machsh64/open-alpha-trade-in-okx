#!/bin/bash
# ============================================================
# Linux/Mac 启动脚本 - 自动检测并启动项目后端 (Uvicorn)
# 支持：自动创建 .conda 环境 + 自动安装 uv
# ============================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONDA_PYTHON="$SCRIPT_DIR/../.conda/bin/python"

echo ""
echo "=========================================="
echo "Starting backend (Unix)"
echo "=========================================="

if [ -f "$CONDA_PYTHON" ]; then
    echo "Using project Python: $CONDA_PYTHON"
else
    echo "Project Python not found at $CONDA_PYTHON"
    echo "Checking for conda or micromamba..."

    if command -v conda >/dev/null 2>&1; then
        CONDA_CMD="conda"
    elif command -v micromamba >/dev/null 2>&1; then
        CONDA_CMD="micromamba"
    else
        echo "Conda/Micromamba not found!"
        echo "Please install Miniconda first:"
        echo "   https://docs.conda.io/en/latest/miniconda.html"
        exit 1
    fi

    echo "Creating new environment with $CONDA_CMD ..."
    $CONDA_CMD create -p "$SCRIPT_DIR/../.conda" python=3.10 -y

    echo "Installing uv..."
    "$CONDA_PYTHON" -m pip install -U pip uv
fi

echo "Syncing dependencies..."
"$CONDA_PYTHON" -m uv sync --quiet

echo "Starting FastAPI server..."
"$CONDA_PYTHON" -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
