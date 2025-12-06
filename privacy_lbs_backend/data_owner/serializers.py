"""
数据所有者序列化器
"""
from rest_framework import serializers
from .models import DataOwner, EncryptedSpatialObject


class DataOwnerSerializer(serializers.ModelSerializer):
    """数据所有者序列化器"""
    
    class Meta:
        model = DataOwner
        fields = ['id', 'owner_id', 'total_objects', 'encrypted_objects', 
                  'index_built', 'index_version', 'created_at']
        read_only_fields = ['id', 'created_at']


class EncryptedSpatialObjectSerializer(serializers.ModelSerializer):
    """加密空间对象序列化器"""
    
    class Meta:
        model = EncryptedSpatialObject
        fields = ['id', 'object_id', 'encrypted_location_x', 'encrypted_location_y',
                  'encrypted_keywords', 'encrypted_document', 'ktree_node_path',
                  'ktree_region', 'created_at']
        read_only_fields = ['id', 'created_at']


class DataUploadSerializer(serializers.Serializer):
    """数据上传序列化器"""
    owner_id = serializers.CharField(max_length=64, required=True)
    objects = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="空间对象列表，每个对象包含object_id, x, y, keywords等字段"
    )
    public_key = serializers.CharField(
        required=True,
        help_text="Paillier公钥（序列化字符串）"
    )

