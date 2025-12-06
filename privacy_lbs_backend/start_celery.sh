#!/bin/bash
# Celery Worker启动脚本（Linux/Mac）
cd "$(dirname "$0")"
celery -A privacy_lbs_backend worker --loglevel=info


