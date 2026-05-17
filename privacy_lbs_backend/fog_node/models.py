from django.db import models
from django.core.validators import MinValueValidator
import json


class FogNode(models.Model):
    """
    Fog Node Information
    Manages the status and configuration of fog node cluster
    """
    
    NODE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
    ]
    
    # Node Identifier
    node_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Node ID'
    )
    
    node_name = models.CharField(
        max_length=128,
        verbose_name='Node Name'
    )
    
    # Node Status
    status = models.CharField(
        max_length=20,
        choices=NODE_STATUS_CHOICES,
        default='inactive',
        db_index=True,
        verbose_name='Node Status'
    )
    
    # Node Address Information
    host = models.CharField(
        max_length=255,
        verbose_name='Host Address',
        help_text='Fog node host address or IP'
    )
    
    port = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Port'
    )
    
    # Node Capacity Information
    max_concurrent_tasks = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name='Max Concurrent Tasks'
    )
    
    current_tasks = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Current Tasks'
    )
    
    # Performance Statistics
    total_tasks_processed = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total Tasks Processed'
    )
    
    average_processing_time = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        verbose_name='Average Processing Time (seconds)'
    )
    
    # Node Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Node Metadata',
        help_text='Store additional configuration information for the node'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    
    last_heartbeat = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Last Heartbeat',
        help_text='Time when the node last reported heartbeat'
    )
    
    class Meta:
        verbose_name = 'Fog Node'
        verbose_name_plural = 'Fog Nodes'
        db_table = 'fog_node'
        indexes = [
            models.Index(fields=['node_id', 'status']),
            models.Index(fields=['status', 'current_tasks']),
        ]
    
    def __str__(self):
        return f"FogNode {self.node_id} - {self.node_name} ({self.get_status_display()})"


class ComputationTask(models.Model):
    """
    Computation Task
    Records computing subtasks distributed from cloud platform to fog nodes
    """
    
    TASK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    # Task Identifier
    task_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Task ID'
    )
    
    # Related Query
    query_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='Query ID',
        help_text='Associated query request ID'
    )
    
    # Related Fog Node
    fog_node = models.ForeignKey(
        FogNode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks',
        verbose_name='Assigned Fog Node'
    )
    
    # Task Type
    task_type = models.CharField(
        max_length=50,
        verbose_name='Task Type',
        help_text='e.g., similarity_computation, distance_calculation, etc.'
    )
    
    # Task Status
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Task Status'
    )
    
    # Task Input Data (encrypted candidate set)
    encrypted_input_data = models.TextField(
        verbose_name='Encrypted Input Data',
        help_text='Encrypted candidate set data stored in JSON format'
    )
    
    # Task Output Result (encrypted scores)
    encrypted_output_data = models.TextField(
        blank=True,
        null=True,
        verbose_name='Encrypted Output Data',
        help_text='Encrypted computation results stored in JSON format'
    )
    
    # Task Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Task Metadata',
        help_text='Store additional information related to the task'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created At'
    )
    
    assigned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Assigned At'
    )
    
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Started At'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Completed At'
    )
    
    class Meta:
        verbose_name = 'Computation Task'
        verbose_name_plural = 'Computation Tasks'
        db_table = 'computation_task'
        indexes = [
            models.Index(fields=['query_id', 'status']),
            models.Index(fields=['fog_node', 'status']),
            models.Index(fields=['task_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Task {self.task_id} for Query {self.query_id} - {self.get_status_display()}"
