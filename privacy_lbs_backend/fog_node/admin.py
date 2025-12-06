from django.contrib import admin
from .models import FogNode, ComputationTask


@admin.register(FogNode)
class FogNodeAdmin(admin.ModelAdmin):
    """雾节点管理"""
    list_display = ['node_id', 'node_name', 'status', 'host', 'port', 'current_tasks', 'last_heartbeat']
    list_filter = ['status', 'created_at']
    search_fields = ['node_id', 'node_name', 'host']
    readonly_fields = ['created_at', 'updated_at', 'last_heartbeat']
    fieldsets = (
        ('基本信息', {
            'fields': ('node_id', 'node_name', 'status')
        }),
        ('网络信息', {
            'fields': ('host', 'port')
        }),
        ('能力信息', {
            'fields': ('max_concurrent_tasks', 'current_tasks')
        }),
        ('性能统计', {
            'fields': ('total_tasks_processed', 'average_processing_time')
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at', 'last_heartbeat'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ComputationTask)
class ComputationTaskAdmin(admin.ModelAdmin):
    """计算任务管理"""
    list_display = ['task_id', 'query_id', 'fog_node', 'task_type', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'task_type', 'created_at']
    search_fields = ['task_id', 'query_id', 'fog_node__node_id']
    readonly_fields = ['task_id', 'created_at', 'assigned_at', 'started_at', 'completed_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('基本信息', {
            'fields': ('task_id', 'query_id', 'fog_node', 'task_type', 'status')
        }),
        ('任务数据', {
            'fields': ('encrypted_input_data', 'encrypted_output_data'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'assigned_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
