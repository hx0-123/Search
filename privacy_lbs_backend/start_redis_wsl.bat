@echo off
REM 在 WSL 中启动 Redis 的批处理脚本
echo ========================================
echo 正在 WSL 中启动 Redis...
echo ========================================
echo.

REM 检查并安装 Redis
echo [1/3] 检查 Redis 是否已安装...
wsl bash -c "if ! command -v redis-server &> /dev/null; then echo 'Redis 未安装，正在安装...'; sudo apt update && sudo apt install redis-server -y; else echo 'Redis 已安装'; fi"

echo.
echo [2/3] 启动 Redis 服务器...
wsl bash -c "sudo service redis-server start"

echo.
echo [3/3] 验证 Redis 是否运行...
wsl bash -c "redis-cli ping"

echo.
echo ========================================
echo 如果看到 PONG，说明 Redis 启动成功！
echo 现在可以在另一个窗口启动 Celery Worker 了
echo ========================================
echo.
echo 按任意键关闭此窗口（Redis 将继续在后台运行）
pause >nul

