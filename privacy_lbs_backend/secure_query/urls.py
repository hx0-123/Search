"""
安全查询URL配置
"""
from django.urls import path
from . import views

app_name = 'secure_query'

urlpatterns = [
    path('initiate/', views.initiate_query, name='initiate_query'),
    path('update_location/', views.update_location, name='update_location'),
    path('<str:query_id>/result/', views.get_query_result, name='get_query_result'),
]

