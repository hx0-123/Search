"""
雾节点 URL 配置
"""
from django.urls import path
from . import views

app_name = 'fog_node'

urlpatterns = [
    # GET /api/nodes/status/  节点监控状态
    path('status/', views.nodes_status, name='nodes_status'),
]

