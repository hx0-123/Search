"""
安全查询序列化器
"""
from rest_framework import serializers
from .models import SecureQuery, UserProfile, QueryLog


class SecureQuerySerializer(serializers.ModelSerializer):
    """安全查询序列化器"""
    
    class Meta:
        model = SecureQuery
        fields = ['id', 'query_id', 'encrypted_location_x', 'encrypted_location_y',
                  'encrypted_keywords', 'text_weight', 'distance_weight', 'top_k',
                  'status', 'is_continuous', 'encrypted_results', 'metadata',
                  'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'query_id', 'status', 'created_at', 
                           'updated_at', 'completed_at']


class QueryInitiateSerializer(serializers.Serializer):
    """查询发起序列化器"""
    encrypted_location_x = serializers.CharField(
        required=True,
        help_text="加密的X坐标"
    )
    encrypted_location_y = serializers.CharField(
        required=True,
        help_text="加密的Y坐标"
    )
    encrypted_keywords = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="加密的关键词列表"
    )
    text_weight = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text="文本相似度权重"
    )
    distance_weight = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text="距离相似度权重"
    )
    top_k = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="返回Top-K个结果"
    )
    is_continuous = serializers.BooleanField(
        default=False,
        help_text="是否为连续查询"
    )


class LocationUpdateSerializer(serializers.Serializer):
    """位置更新序列化器"""
    query_id = serializers.CharField(
        required=True,
        help_text="查询ID"
    )
    encrypted_location_x = serializers.CharField(
        required=True,
        help_text="新的加密X坐标"
    )
    encrypted_location_y = serializers.CharField(
        required=True,
        help_text="新的加密Y坐标"
    )


class QueryResultSerializer(serializers.Serializer):
    """查询结果序列化器"""
    query_id = serializers.CharField()
    status = serializers.CharField()
    encrypted_results = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    message = serializers.CharField(required=False)

