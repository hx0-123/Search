from django.contrib import admin
from .models import UserProfile, SecureQuery, QueryLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Management"""
    list_display = ['user', 'phone', 'default_text_weight', 'default_distance_weight', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone')
        }),
        ('Preferences', {
            'fields': ('default_text_weight', 'default_distance_weight')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecureQuery)
class SecureQueryAdmin(admin.ModelAdmin):
    """Secure Query Management"""
    list_display = ['query_id', 'user', 'status', 'is_continuous', 'top_k', 'created_at', 'completed_at']
    list_filter = ['status', 'is_continuous', 'created_at']
    search_fields = ['query_id', 'user__username']
    readonly_fields = ['query_id', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('query_id', 'user', 'status', 'is_continuous')
        }),
        ('Encrypted Query Data', {
            'fields': ('encrypted_location_x', 'encrypted_location_y', 'encrypted_keywords'),
            'classes': ('collapse',)
        }),
        ('Query Parameters', {
            'fields': ('text_weight', 'distance_weight', 'top_k')
        }),
        ('Query Results', {
            'fields': ('encrypted_results', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """Query Log Management"""
    list_display = ['query', 'log_type', 'created_at']
    list_filter = ['log_type', 'created_at']
    search_fields = ['query__query_id', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('query', 'log_type', 'message')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
