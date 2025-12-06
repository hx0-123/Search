@echo off
REM Celery Worker启动脚本（Windows）
cd /d %~dp0
echo Starting Celery Worker...
echo Current directory: %CD%
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
pause

