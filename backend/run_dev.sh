#!/bin/bash
# Linux/Mac启动脚本 - 用于开发环境
# 自动查找项目Python并启动uvicorn

export PYTHONPATH="$(pwd)"

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查 .conda/bin/python 是否存在
if [ -f "$SCRIPT_DIR/../.conda/bin/python" ]; then
    echo "Using project Python: $SCRIPT_DIR/../.conda/bin/python"
    "$SCRIPT_DIR/../.conda/bin/python" -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
else
    echo "Project Python not found at ../.conda/bin/python"
    echo "Please run: pnpm install:all"
    echo "Or using system Python"
    python3 -m uvicorn main:app --reload --port 5611 --host 0.0.0.0
fi

