from django.contrib import admin
from .models import DataOwner, EncryptedSpatialObject, IndexMetadata


@admin.register(DataOwner)
class DataOwnerAdmin(admin.ModelAdmin):
    """Data Owner Management"""
    list_display = ['owner_id', 'user', 'total_objects', 'encrypted_objects', 'index_built', 'created_at']
    list_filter = ['index_built', 'created_at']
    search_fields = ['owner_id', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'owner_id')
        }),
        ('Encryption Information', {
            'fields': ('public_key',),
            'classes': ('collapse',)
        }),
        ('Data Statistics', {
            'fields': ('total_objects', 'encrypted_objects')
        }),
        ('Index Status', {
            'fields': ('index_built', 'index_version')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EncryptedSpatialObject)
class EncryptedSpatialObjectAdmin(admin.ModelAdmin):
    """Encrypted Spatial Object Management"""
    list_display = ['object_id', 'data_owner', 'ktree_region', 'ktree_node_path', 'created_at']
    list_filter = ['data_owner', 'ktree_region', 'created_at']
    search_fields = ['object_id', 'data_owner__owner_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('data_owner', 'object_id')
        }),
        ('Original Location (Debug Only)', {
            'fields': ('original_x', 'original_y'),
            'classes': ('collapse',),
            'description': 'This field should be removed in production'
        }),
        ('Encrypted Location', {
            'fields': ('encrypted_location_x', 'encrypted_location_y'),
            'classes': ('collapse',)
        }),
        ('Encrypted Data', {
            'fields': ('encrypted_keywords', 'encrypted_document'),
            'classes': ('collapse',)
        }),
        ('Index Information', {
            'fields': ('ktree_node_path', 'ktree_region')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(IndexMetadata)
class IndexMetadataAdmin(admin.ModelAdmin):
    """Index Metadata Management"""
    list_display = ['data_owner', 'ktree_depth', 'build_status', 'index_storage_type', 'updated_at']
    list_filter = ['build_status', 'index_storage_type', 'updated_at']
    search_fields = ['data_owner__owner_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('data_owner',)
        }),
        ('KTree Information', {
            'fields': ('ktree_depth', 'ktree_node_count', 'ktree_leaf_count')
        }),
        ('Spatial Domain Information', {
            'fields': ('spatial_domain_x_min', 'spatial_domain_x_max',
                      'spatial_domain_y_min', 'spatial_domain_y_max')
        }),
        ('AssetTree Information', {
            'fields': ('assettree_size',)
        }),
        ('Storage Information', {
            'fields': ('index_storage_type', 'index_storage_path')
        }),
        ('Build Status', {
            'fields': ('build_status', 'build_started_at', 'build_completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
