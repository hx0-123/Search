"""
Celery配置
"""
import os
from celery import Celery

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'privacy_lbs_backend.settings')

app = Celery('privacy_lbs_backend')

# 从Django设置中加载Celery配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

