from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
import json


class DataOwner(models.Model):
    """
    数据所有者信息
    管理数据上传、加密和索引构建
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='data_owner',
        verbose_name='关联用户'
    )
    
    # 数据所有者标识
    owner_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='所有者ID'
    )
    
    # 公钥信息 (用于同态加密)
    public_key = models.TextField(
        verbose_name='公钥',
        help_text='Paillier同态加密的公钥，用于加密数据'
    )
    
    # 数据统计信息
    total_objects = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='总对象数'
    )
    
    encrypted_objects = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='已加密对象数'
    )
    
    # 索引构建状态
    index_built = models.BooleanField(
        default=False,
        verbose_name='索引是否已构建',
        help_text='KASTree索引是否已构建完成'
    )
    
    index_version = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='索引版本',
        help_text='索引的版本号，用于版本管理'
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
        verbose_name = '数据所有者'
        verbose_name_plural = '数据所有者'
        db_table = 'data_owner'
        indexes = [
            models.Index(fields=['owner_id']),
            models.Index(fields=['index_built']),
        ]
    
    def __str__(self):
        return f"DataOwner {self.owner_id} - {self.user.username}"


class EncryptedSpatialObject(models.Model):
    """
    存储由数据所有者加密后的空间文本对象
    包含密文位置、密文关键词集合等信息
    """
    
    # 关联数据所有者
    data_owner = models.ForeignKey(
        DataOwner,
        on_delete=models.CASCADE,
        related_name='spatial_objects',
        verbose_name='数据所有者'
    )
    
    # 对象唯一标识
    object_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name='对象ID',
        help_text='空间对象的唯一标识符'
    )
    
    # 原始位置信息 (可选，用于调试，生产环境应删除)
    original_x = models.FloatField(
        blank=True,
        null=True,
        verbose_name='原始X坐标',
        help_text='仅用于开发调试，生产环境应删除此字段'
    )
    
    original_y = models.FloatField(
        blank=True,
        null=True,
        verbose_name='原始Y坐标',
        help_text='仅用于开发调试，生产环境应删除此字段'
    )
    
    # 加密位置信息 (密文)
    encrypted_location_x = models.TextField(
        verbose_name='加密X坐标',
        help_text='使用Paillier同态加密的X坐标密文'
    )
    
    encrypted_location_y = models.TextField(
        verbose_name='加密Y坐标',
        help_text='使用Paillier同态加密的Y坐标密文'
    )
    
    # 加密关键词集合 (密文)
    encrypted_keywords = models.TextField(
        verbose_name='加密关键词集合',
        help_text='JSON格式存储的加密关键词列表'
    )
    
    # 对象文档信息 (加密)
    encrypted_document = models.TextField(
        blank=True,
        null=True,
        verbose_name='加密文档',
        help_text='对象的加密文档内容或标识'
    )
    
    # 对象元数据
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='对象元数据',
        help_text='存储对象的额外信息，如类别、标签等'
    )
    
    # KTree节点关联信息
    ktree_node_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='KTree节点路径',
        help_text='该对象在KTree中的路径，用于索引检索'
    )
    
    ktree_region = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='KTree区域编号',
        help_text='对象所属的KTree区域编号(0-3)'
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
    
    class Meta:
        verbose_name = '加密空间对象'
        verbose_name_plural = '加密空间对象'
        db_table = 'encrypted_spatial_object'
        indexes = [
            models.Index(fields=['data_owner', 'object_id']),
            models.Index(fields=['ktree_region', 'ktree_node_path']),
            models.Index(fields=['created_at']),
        ]
        # 确保同一数据所有者的对象ID唯一
        unique_together = [['data_owner', 'object_id']]
    
    def __str__(self):
        return f"Object {self.object_id} by {self.data_owner.owner_id}"
    
    def get_encrypted_keywords_list(self):
        """解析加密关键词列表"""
        try:
            return json.loads(self.encrypted_keywords)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_encrypted_keywords_list(self, keywords_list):
        """设置加密关键词列表"""
        self.encrypted_keywords = json.dumps(keywords_list, ensure_ascii=False)


class IndexMetadata(models.Model):
    """
    KASTree索引元数据
    由于KTree和AssetTree结构复杂且涉及大量密文操作，
    实际索引数据存储在Redis或Cassandra中，
    此模型仅存储索引的元数据信息
    """
    
    # 关联数据所有者
    data_owner = models.OneToOneField(
        DataOwner,
        on_delete=models.CASCADE,
        related_name='index_metadata',
        verbose_name='数据所有者'
    )
    
    # KTree元数据
    ktree_depth = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree深度',
        help_text='KTree的深度(高度)'
    )
    
    ktree_node_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree节点数'
    )
    
    ktree_leaf_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='KTree叶子节点数'
    )
    
    # 空间域信息
    spatial_domain_x_min = models.FloatField(
        verbose_name='X轴最小值',
        help_text='数据空间域的X轴最小值'
    )
    
    spatial_domain_x_max = models.FloatField(
        verbose_name='X轴最大值',
        help_text='数据空间域的X轴最大值'
    )
    
    spatial_domain_y_min = models.FloatField(
        verbose_name='Y轴最小值',
        help_text='数据空间域的Y轴最小值'
    )
    
    spatial_domain_y_max = models.FloatField(
        verbose_name='Y轴最大值',
        help_text='数据空间域的Y轴最大值'
    )
    
    # AssetTree元数据
    assettree_size = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='AssetTree大小',
        help_text='AssetTree的节点数量'
    )
    
    # 索引存储位置
    index_storage_type = models.CharField(
        max_length=20,
        choices=[
            ('redis', 'Redis'),
            ('cassandra', 'Cassandra'),
            ('file', '文件系统'),
            ('memory', '内存'),
        ],
        default='redis',
        verbose_name='索引存储类型'
    )
    
    index_storage_path = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name='索引存储路径',
        help_text='索引在存储系统中的路径或键名'
    )
    
    # 索引构建信息
    build_status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', '未开始'),
            ('building', '构建中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ],
        default='not_started',
        verbose_name='构建状态'
    )
    
    build_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='构建开始时间'
    )
    
    build_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='构建完成时间'
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
        verbose_name = '索引元数据'
        verbose_name_plural = '索引元数据'
        db_table = 'index_metadata'
    
    def __str__(self):
        return f"IndexMetadata for {self.data_owner.owner_id} - {self.get_build_status_display()}"
