"""
Data Owner Serializers
"""
from rest_framework import serializers
from .models import DataOwner, EncryptedSpatialObject, KeyPair


class KeyPairStatusSerializer(serializers.ModelSerializer):
    """Key pair status serializer (does not expose private key)"""

    class Meta:
        model = KeyPair
        fields = ['id', 'key_size', 'public_key_digest', 'gen_time_ms', 'is_active', 'created_at']
        read_only_fields = fields


class DataOwnerSerializer(serializers.ModelSerializer):
    """Data owner serializer"""

    class Meta:
        model = DataOwner
        fields = ['id', 'owner_id', 'total_objects', 'encrypted_objects',
                  'index_built', 'index_version', 'created_at']
        read_only_fields = ['id', 'created_at']


class EncryptedSpatialObjectSerializer(serializers.ModelSerializer):
    """Encrypted spatial object serializer"""

    class Meta:
        model = EncryptedSpatialObject
        fields = ['id', 'object_id', 'encrypted_location_x', 'encrypted_location_y',
                  'encrypted_keywords', 'encrypted_document', 'ktree_node_path',
                  'ktree_region', 'created_at']
        read_only_fields = ['id', 'created_at']


class SpatialObjectSerializer(serializers.Serializer):
    """Spatial object serializer"""
    object_id = serializers.CharField(required=False, allow_blank=True, help_text="Object ID, auto-generated if not provided")
    x = serializers.FloatField(required=True, help_text="X coordinate (longitude)")
    y = serializers.FloatField(required=True, help_text="Y coordinate (latitude)")
    keywords = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        allow_empty=True,
        help_text="Keyword list"
    )
    document = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text="Object document description"
    )


class DataUploadSerializer(serializers.Serializer):
    """Data upload serializer"""
    owner_id = serializers.CharField(max_length=64, required=True, help_text="Data owner ID")
    objects = serializers.ListField(
        child=SpatialObjectSerializer(),
        required=True,
        min_length=1,
        help_text="Spatial object list, each object must contain x and y coordinates"
    )
    public_key = serializers.CharField(
        required=False,          # Made optional: upload_csv gets active key from database automatically
        allow_blank=True,
        default='',
        help_text="Paillier public key (serialized string); uses active key pair from database if not provided"
    )

    def validate(self, data):
        """Overall validation: if public_key is empty, get active key from database"""
        if not data.get('public_key'):
            from .models import KeyPair
            kp = KeyPair.objects.filter(is_active=True).order_by('-created_at').first()
            if kp is None:
                raise serializers.ValidationError(
                    {'public_key': 'No key pair generated yet, please call POST /api/data/keygen/ first'}
                )
            data['public_key'] = kp.public_key
        return data

    def validate_objects(self, value):
        """Validate object list"""
        if not value:
            raise serializers.ValidationError("Object list cannot be empty")
        return value

