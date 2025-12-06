from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class UserProfile(models.Model):
    """
    存储用户基本信息
    扩展Django默认User模型，添加用户相关的额外信息
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='关联用户'
    )
    
    # 用户基本信息
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='手机号'
    )
    
    # 用户偏好设置
    default_text_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='默认文本权重',
        help_text='文本相似度权重，范围0-1'
    )
    
    default_distance_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='默认距离权重',
        help_text='距离相似度权重，范围0-1'
    )
    
    # 用户状态
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否激活'
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
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
        db_table = 'user_profile'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Profile"


class SecureQuery(models.Model):
    """
    存储用户发起的加密查询请求
    支持连续查询、实时位置更新等功能
    """
    
    QUERY_STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='secure_queries',
        verbose_name='查询用户'
    )
    
    # 查询唯一标识
    query_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='查询ID',
        help_text='唯一标识一次查询请求'
    )
    
    # 加密查询位置 (密文)
    encrypted_location_x = models.TextField(
        verbose_name='加密X坐标',
        help_text='使用Paillier同态加密的X坐标密文'
    )
    
    encrypted_location_y = models.TextField(
        verbose_name='加密Y坐标',
        help_text='使用Paillier同态加密的Y坐标密文'
    )
    
    # 加密查询关键词集合 (密文)
    encrypted_keywords = models.TextField(
        verbose_name='加密关键词集合',
        help_text='JSON格式存储的加密关键词列表'
    )
    
    # 查询参数
    text_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='文本权重',
        help_text='文本相似度权重'
    )
    
    distance_weight = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='距离权重',
        help_text='距离相似度权重'
    )
    
    top_k = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Top-K结果数',
        help_text='返回前K个最相似的结果'
    )
    
    # 查询状态
    status = models.CharField(
        max_length=20,
        choices=QUERY_STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='查询状态'
    )
    
    # 是否为连续查询
    is_continuous = models.BooleanField(
        default=False,
        verbose_name='是否连续查询',
        help_text='是否为连续空间查询，需要实时更新位置'
    )
    
    # 查询结果 (加密状态)
    encrypted_results = models.TextField(
        blank=True,
        null=True,
        verbose_name='加密查询结果',
        help_text='JSON格式存储的加密Top-K结果'
    )
    
    # 查询元数据
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='查询元数据',
        help_text='存储查询相关的额外信息，如查询时间、处理节点等'
    )
    
    # 时间戳
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='创建时间'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='完成时间'
    )
    
    class Meta:
        verbose_name = '安全查询'
        verbose_name_plural = '安全查询'
        db_table = 'secure_query'
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['query_id']),
            models.Index(fields=['is_continuous', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query {self.query_id} by {self.user.username} - {self.get_status_display()}"
    
    def get_encrypted_keywords_list(self):
        """解析加密关键词列表"""
        try:
            return json.loads(self.encrypted_keywords)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_encrypted_keywords_list(self, keywords_list):
        """设置加密关键词列表"""
        self.encrypted_keywords = json.dumps(keywords_list, ensure_ascii=False)


class QueryLog(models.Model):
    """
    查询日志，用于记录查询历史和分析
    """
    query = models.ForeignKey(
        SecureQuery,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='关联查询'
    )
    
    log_type = models.CharField(
        max_length=50,
        verbose_name='日志类型',
        help_text='如：query_received, index_search, fog_computation, result_returned等'
    )
    
    message = models.TextField(
        verbose_name='日志消息'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='日志元数据'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='创建时间'
    )
    
    class Meta:
        verbose_name = '查询日志'
        verbose_name_plural = '查询日志'
        db_table = 'query_log'
        indexes = [
            models.Index(fields=['query', 'created_at']),
            models.Index(fields=['log_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Log for {self.query.query_id} - {self.log_type}"
