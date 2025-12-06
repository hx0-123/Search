#!/bin/bash
# 在 WSL 中启动 Redis 的脚本

echo "检查 Redis 是否已安装..."
if ! command -v redis-server &> /dev/null; then
    echo "Redis 未安装，正在安装..."
    sudo apt update
    sudo apt install redis-server -y
fi

echo "启动 Redis 服务器..."
sudo service redis-server start

echo "验证 Redis 是否运行..."
redis-cli ping

if [ $? -eq 0 ]; then
    echo "✅ Redis 启动成功！"
    echo "Redis 正在运行，可以在 Windows 中启动 Celery Worker 了"
else
    echo "❌ Redis 启动失败"
    exit 1
fi

