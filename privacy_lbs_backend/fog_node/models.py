from django.db import models
from django.core.validators import MinValueValidator
import json


class FogNode(models.Model):
    """
    雾节点信息
    管理雾节点集群的状态和配置
    """
    
    NODE_STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('maintenance', '维护中'),
        ('error', '错误'),
    ]
    
    # 节点标识
    node_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='节点ID'
    )
    
    node_name = models.CharField(
        max_length=128,
        verbose_name='节点名称'
    )
    
    # 节点状态
    status = models.CharField(
        max_length=20,
        choices=NODE_STATUS_CHOICES,
        default='inactive',
        db_index=True,
        verbose_name='节点状态'
    )
    
    # 节点地址信息
    host = models.CharField(
        max_length=255,
        verbose_name='主机地址',
        help_text='雾节点的主机地址或IP'
    )
    
    port = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='端口号'
    )
    
    # 节点能力信息
    max_concurrent_tasks = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name='最大并发任务数'
    )
    
    current_tasks = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='当前任务数'
    )
    
    # 性能统计
    total_tasks_processed = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='总处理任务数'
    )
    
    average_processing_time = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        verbose_name='平均处理时间(秒)'
    )
    
    # 节点元数据
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='节点元数据',
        help_text='存储节点的额外配置信息'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    last_heartbeat = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='最后心跳时间',
        help_text='节点最后上报心跳的时间'
    )
    
    class Meta:
        verbose_name = '雾节点'
        verbose_name_plural = '雾节点'
        db_table = 'fog_node'
        indexes = [
            models.Index(fields=['node_id', 'status']),
            models.Index(fields=['status', 'current_tasks']),
        ]
    
    def __str__(self):
        return f"FogNode {self.node_id} - {self.node_name} ({self.get_status_display()})"


class ComputationTask(models.Model):
    """
    计算任务
    记录云平台分发给雾节点的计算子任务
    """
    
    TASK_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('assigned', '已分配'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('timeout', '超时'),
    ]
    
    # 任务标识
    task_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='任务ID'
    )
    
    # 关联查询
    query_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='查询ID',
        help_text='关联的查询请求ID'
    )
    
    # 关联雾节点
    fog_node = models.ForeignKey(
        FogNode,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks',
        verbose_name='分配的雾节点'
    )
    
    # 任务类型
    task_type = models.CharField(
        max_length=50,
        verbose_name='任务类型',
        help_text='如：similarity_computation, distance_calculation等'
    )
    
    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=TASK_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='任务状态'
    )
    
    # 任务输入数据 (加密的候选集)
    encrypted_input_data = models.TextField(
        verbose_name='加密输入数据',
        help_text='JSON格式存储的加密候选集数据'
    )
    
    # 任务输出结果 (加密的评分)
    encrypted_output_data = models.TextField(
        blank=True,
        null=True,
        verbose_name='加密输出数据',
        help_text='JSON格式存储的加密计算结果'
    )
    
    # 任务元数据
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='任务元数据',
        help_text='存储任务相关的额外信息'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='创建时间'
    )
    
    assigned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='分配时间'
    )
    
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='开始处理时间'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='完成时间'
    )
    
    class Meta:
        verbose_name = '计算任务'
        verbose_name_plural = '计算任务'
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
