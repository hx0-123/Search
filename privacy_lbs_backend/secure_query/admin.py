from django.contrib import admin
from .models import UserProfile, SecureQuery, QueryLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """用户资料管理"""
    list_display = ['user', 'phone', 'default_text_weight', 'default_distance_weight', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('用户信息', {
            'fields': ('user', 'phone')
        }),
        ('偏好设置', {
            'fields': ('default_text_weight', 'default_distance_weight')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecureQuery)
class SecureQueryAdmin(admin.ModelAdmin):
    """安全查询管理"""
    list_display = ['query_id', 'user', 'status', 'is_continuous', 'top_k', 'created_at', 'completed_at']
    list_filter = ['status', 'is_continuous', 'created_at']
    search_fields = ['query_id', 'user__username']
    readonly_fields = ['query_id', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('基本信息', {
            'fields': ('query_id', 'user', 'status', 'is_continuous')
        }),
        ('加密查询数据', {
            'fields': ('encrypted_location_x', 'encrypted_location_y', 'encrypted_keywords'),
            'classes': ('collapse',)
        }),
        ('查询参数', {
            'fields': ('text_weight', 'distance_weight', 'top_k')
        }),
        ('查询结果', {
            'fields': ('encrypted_results', 'metadata'),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """查询日志管理"""
    list_display = ['query', 'log_type', 'created_at']
    list_filter = ['log_type', 'created_at']
    search_fields = ['query__query_id', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('基本信息', {
            'fields': ('query', 'log_type', 'message')
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at',)
        }),
    )
