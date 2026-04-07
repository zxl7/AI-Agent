#!/bin/bash

# ==========================================
# Alpha Agent 全栈一键启动脚本
# ==========================================

# 设置遇到错误时退出
set -e

echo "=========================================="
echo "🚀 正在启动 Alpha Agent 全栈项目..."
echo "=========================================="

# 捕获 Ctrl+C (SIGINT) 和 kill (SIGTERM) 信号，以便退出时清理所有后台进程
trap 'echo -e "\n🛑 正在停止所有服务..."; kill 0; exit 0' SIGINT SIGTERM

# 1. 启动后端服务 (后台运行)
echo "📦 [1/2] 启动后端服务 (NestJS)..."
cd alpha-agent-backend
npm run start:dev &
BACKEND_PID=$!
cd ..

# 等待2秒确保后端端口启动
sleep 2

# 2. 启动前端服务 (后台运行)
echo "🎨 [2/2] 启动前端服务 (Vite)..."
cd alpha-agent-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "=========================================="
echo "✅ 服务已全部启动！"
echo "👉 前端地址: http://localhost:5173"
echo "👉 后端地址: http://localhost:3000"
echo "👉 按 Ctrl+C 可以同时停止前后端服务"
echo "=========================================="

# 等待后台进程，防止脚本直接退出
wait
