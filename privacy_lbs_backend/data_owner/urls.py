"""
数据所有者URL配置
"""
from django.urls import path
from . import views

app_name = 'data_owner'

urlpatterns = [
    path('upload/', views.upload_data, name='upload_data'),
]

