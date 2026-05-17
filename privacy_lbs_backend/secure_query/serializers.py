"""
Secure Query Serializers
"""
from rest_framework import serializers
from .models import SecureQuery, UserProfile, QueryLog


class SecureQuerySerializer(serializers.ModelSerializer):
    """Secure Query Serializer"""
    
    class Meta:
        model = SecureQuery
        fields = ['id', 'query_id', 'encrypted_location_x', 'encrypted_location_y',
                  'encrypted_keywords', 'text_weight', 'distance_weight', 'top_k',
                  'status', 'is_continuous', 'encrypted_results', 'metadata',
                  'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'query_id', 'status', 'created_at', 
                           'updated_at', 'completed_at']


class QueryInitiateSerializer(serializers.Serializer):
    """Query Initiation Serializer"""
    encrypted_location_x = serializers.CharField(
        required=True,
        help_text="Encrypted X coordinate"
    )
    encrypted_location_y = serializers.CharField(
        required=True,
        help_text="Encrypted Y coordinate"
    )
    encrypted_keywords = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="Encrypted keyword list"
    )
    text_weight = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text="Text similarity weight"
    )
    distance_weight = serializers.FloatField(
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        help_text="Distance similarity weight"
    )
    top_k = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=100,
        help_text="Return Top-K results"
    )
    is_continuous = serializers.BooleanField(
        default=False,
        help_text="Whether it's a continuous query"
    )


class LocationUpdateSerializer(serializers.Serializer):
    """Location Update Serializer"""
    query_id = serializers.CharField(
        required=True,
        help_text="Query ID"
    )
    encrypted_location_x = serializers.CharField(
        required=True,
        help_text="New encrypted X coordinate"
    )
    encrypted_location_y = serializers.CharField(
        required=True,
        help_text="New encrypted Y coordinate"
    )


class QueryResultSerializer(serializers.Serializer):
    """Query Result Serializer"""
    query_id = serializers.CharField()
    status = serializers.CharField()
    encrypted_results = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    message = serializers.CharField(required=False)

