@echo off
REM Vue项目开发服务器启动脚本
cd /d %~dp0
echo 正在启动Vue开发服务器...
echo 当前目录: %CD%
echo.
npm run dev
pause










