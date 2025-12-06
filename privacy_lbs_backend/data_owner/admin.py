from django.contrib import admin
from .models import DataOwner, EncryptedSpatialObject, IndexMetadata


@admin.register(DataOwner)
class DataOwnerAdmin(admin.ModelAdmin):
    """数据所有者管理"""
    list_display = ['owner_id', 'user', 'total_objects', 'encrypted_objects', 'index_built', 'created_at']
    list_filter = ['index_built', 'created_at']
    search_fields = ['owner_id', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'owner_id')
        }),
        ('加密信息', {
            'fields': ('public_key',),
            'classes': ('collapse',)
        }),
        ('数据统计', {
            'fields': ('total_objects', 'encrypted_objects')
        }),
        ('索引状态', {
            'fields': ('index_built', 'index_version')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EncryptedSpatialObject)
class EncryptedSpatialObjectAdmin(admin.ModelAdmin):
    """加密空间对象管理"""
    list_display = ['object_id', 'data_owner', 'ktree_region', 'ktree_node_path', 'created_at']
    list_filter = ['data_owner', 'ktree_region', 'created_at']
    search_fields = ['object_id', 'data_owner__owner_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('基本信息', {
            'fields': ('data_owner', 'object_id')
        }),
        ('原始位置(仅调试)', {
            'fields': ('original_x', 'original_y'),
            'classes': ('collapse',),
            'description': '生产环境应删除此字段'
        }),
        ('加密位置', {
            'fields': ('encrypted_location_x', 'encrypted_location_y'),
            'classes': ('collapse',)
        }),
        ('加密数据', {
            'fields': ('encrypted_keywords', 'encrypted_document'),
            'classes': ('collapse',)
        }),
        ('索引信息', {
            'fields': ('ktree_node_path', 'ktree_region')
        }),
        ('元数据', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IndexMetadata)
class IndexMetadataAdmin(admin.ModelAdmin):
    """索引元数据管理"""
    list_display = ['data_owner', 'ktree_depth', 'build_status', 'index_storage_type', 'updated_at']
    list_filter = ['build_status', 'index_storage_type', 'updated_at']
    search_fields = ['data_owner__owner_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('data_owner',)
        }),
        ('KTree信息', {
            'fields': ('ktree_depth', 'ktree_node_count', 'ktree_leaf_count')
        }),
        ('空间域信息', {
            'fields': ('spatial_domain_x_min', 'spatial_domain_x_max', 
                      'spatial_domain_y_min', 'spatial_domain_y_max')
        }),
        ('AssetTree信息', {
            'fields': ('assettree_size',)
        }),
        ('存储信息', {
            'fields': ('index_storage_type', 'index_storage_path')
        }),
        ('构建状态', {
            'fields': ('build_status', 'build_started_at', 'build_completed_at')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
