#!/bin/bash
# 开发环境启动脚本

# 启动后端（后台运行）
echo "🚀 Starting FastAPI backend..."
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "🎨 Starting React frontend..."
cd frontend
npm start

# 前端关闭后杀死后端
kill $BACKEND_PID
